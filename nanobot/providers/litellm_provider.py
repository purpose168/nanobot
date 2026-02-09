"""用于多提供商支持的 LiteLLM 提供商实现。"""

import json
import os
from typing import Any

import litellm
from litellm import acompletion
from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from nanobot.providers.registry import find_by_model, find_gateway


class LiteLLMProvider(LLMProvider):
    """
    使用 LiteLLM 的 LLM 提供商，支持多提供商。
    
    通过统一接口支持 OpenRouter、Anthropic、OpenAI、Gemini
    和许多其他提供商。提供商特定的逻辑由注册表驱动
    （参见 providers/registry.py）——此处不需要 if-elif 链。
    """
    
    def __init__(
        self, 
        api_key: str | None = None, 
        api_base: str | None = None,
        default_model: str = "anthropic/claude-opus-4-5",
        extra_headers: dict[str, str] | None = None,
    ):
        super().__init__(api_key, api_base)
        self.default_model = default_model
        self.extra_headers = extra_headers or {}
        
        # 从 api_key 和 api_base 检测网关 / 本地部署
        self._gateway = find_gateway(api_key, api_base)
        
        # 向后兼容的标志（由测试和可能的外部代码使用）
        self.is_openrouter = bool(self._gateway and self._gateway.name == "openrouter")
        self.is_aihubmix = bool(self._gateway and self._gateway.name == "aihubmix")
        self.is_vllm = bool(self._gateway and self._gateway.is_local)
        
        # 配置环境变量
        if api_key:
            self._setup_env(api_key, api_base, default_model)
        
        if api_base:
            litellm.api_base = api_base
        
        # 禁用 LiteLLM 日志噪音
        litellm.suppress_debug_info = True
    
    def _setup_env(self, api_key: str, api_base: str | None, model: str) -> None:
        """根据检测到的提供商设置环境变量。"""
        if self._gateway:
            # 网关 / 本地：直接设置（不使用 setdefault）
            os.environ[self._gateway.env_key] = api_key
            return
        
        # 标准提供商：按模型名称匹配
        spec = find_by_model(model)
        if spec:
            os.environ.setdefault(spec.env_key, api_key)
            # 解析 env_extras 占位符：
            #   {api_key}  → 用户的 API 密钥
            #   {api_base} → 用户的 api_base，回退到 spec.default_api_base
            effective_base = api_base or spec.default_api_base
            for env_name, env_val in spec.env_extras:
                resolved = env_val.replace("{api_key}", api_key)
                resolved = resolved.replace("{api_base}", effective_base)
                os.environ.setdefault(env_name, resolved)
    
    def _resolve_model(self, model: str) -> str:
        """通过应用提供商/网关前缀解析模型名称。"""
        if self._gateway:
            # 网关模式：应用网关前缀，跳过提供商特定的前缀
            prefix = self._gateway.litellm_prefix
            if self._gateway.strip_model_prefix:
                model = model.split("/")[-1]
            if prefix and not model.startswith(f"{prefix}/"):
                model = f"{prefix}/{model}"
            return model
        
        # 标准模式：为已知提供商自动添加前缀
        spec = find_by_model(model)
        if spec and spec.litellm_prefix:
            if not any(model.startswith(s) for s in spec.skip_prefixes):
                model = f"{spec.litellm_prefix}/{model}"
        
        return model
    
    def _apply_model_overrides(self, model: str, kwargs: dict[str, Any]) -> None:
        """从注册表应用模型特定的参数覆盖。"""
        model_lower = model.lower()
        spec = find_by_model(model)
        if spec:
            for pattern, overrides in spec.model_overrides:
                if pattern in model_lower:
                    kwargs.update(overrides)
                    return
    
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        通过 LiteLLM 发送聊天完成请求。
        
        参数:
            messages: 包含 'role' 和 'content' 的消息字典列表。
            tools: OpenAI 格式的可选工具定义列表。
            model: 模型标识符（例如，'anthropic/claude-sonnet-4-5'）。
            max_tokens: 响应中的最大令牌数。
            temperature: 采样温度。
        
        返回:
            包含内容和/或工具调用的 LLMResponse。
        """
        model = self._resolve_model(model or self.default_model)
        
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # 应用模型特定的覆盖（例如 kimi-k2.5 的温度）
        self._apply_model_overrides(model, kwargs)
        
        # 直接传递 api_base 用于自定义端点（vLLM 等）
        if self.api_base:
            kwargs["api_base"] = self.api_base
        
        # 传递额外的头信息（例如 AiHubMix 的 APP-Code）
        if self.extra_headers:
            kwargs["extra_headers"] = self.extra_headers
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            response = await acompletion(**kwargs)
            return self._parse_response(response)
        except Exception as e:
            # 将错误作为内容返回以进行优雅处理
            return LLMResponse(
                content=f"Error calling LLM: {str(e)}",
                finish_reason="error",
            )
    
    def _parse_response(self, response: Any) -> LLMResponse:
        """将 LiteLLM 响应解析为我们的标准格式。"""
        choice = response.choices[0]
        message = choice.message
        
        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                # 从 JSON 字符串解析参数（如果需要）
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                
                tool_calls.append(ToolCallRequest(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))
        
        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
        )
    
    def get_default_model(self) -> str:
        """获取默认模型。"""
        return self.default_model
