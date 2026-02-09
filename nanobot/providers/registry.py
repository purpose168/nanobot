"""
提供商注册表 — LLM 提供商元数据的单一数据源。

添加新提供商：
  1. 在下方的 PROVIDERS 中添加 ProviderSpec。
  2. 在 config/schema.py 的 ProvidersConfig 中添加字段。
  完成。环境变量、前缀、配置匹配、状态显示都由此派生。

顺序很重要 — 它控制匹配优先级和回退。网关优先。
每个条目写出所有字段，以便您可以复制粘贴作为模板。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderSpec:
    """一个 LLM 提供商的元数据。参见下方的 PROVIDERS 以获取真实示例。

    env_extras 值中的占位符：
      {api_key}  — 用户的 API 密钥
      {api_base} — 配置文件中的 api_base，或此规范的 default_api_base
    """

    # 标识
    name: str                       # 配置字段名，例如 "dashscope"
    keywords: tuple[str, ...]       # 用于匹配的模型名称关键字（小写）
    env_key: str                    # LiteLLM 环境变量，例如 "DASHSCOPE_API_KEY"
    display_name: str = ""          # 在 `nanobot status` 中显示

    # 模型前缀
    litellm_prefix: str = ""                 # "dashscope" → 模型变为 "dashscope/{model}"
    skip_prefixes: tuple[str, ...] = ()      # 如果模型已经以这些开头，则不要添加前缀

    # 额外环境变量，例如 (("ZHIPUAI_API_KEY", "{api_key}"),)
    env_extras: tuple[tuple[str, str], ...] = ()

    # 网关 / 本地检测
    is_gateway: bool = False                 # 路由任何模型（OpenRouter、AiHubMix）
    is_local: bool = False                   # 本地部署（vLLM、Ollama）
    detect_by_key_prefix: str = ""           # 匹配 api_key 前缀，例如 "sk-or-"
    detect_by_base_keyword: str = ""         # 匹配 api_base URL 中的子字符串
    default_api_base: str = ""               # 回退基础 URL

    # 网关行为
    strip_model_prefix: bool = False         # 在重新添加前缀之前去除 "provider/"

    # 按模型参数覆盖，例如 (("kimi-k2.5", {"temperature": 1.0}),)
    model_overrides: tuple[tuple[str, dict[str, Any]], ...] = ()

    @property
    def label(self) -> str:
        return self.display_name or self.name.title()


# ---------------------------------------------------------------------------
# PROVIDERS — 注册表。顺序 = 优先级。复制任何条目作为模板。
# ---------------------------------------------------------------------------

PROVIDERS: tuple[ProviderSpec, ...] = (

    # === 网关（通过 api_key / api_base 检测，而非模型名称）=========
    # 网关可以路由任何模型，所以它们在回退中胜出。

    # OpenRouter：全局网关，密钥以 "sk-or-" 开头
    ProviderSpec(
        name="openrouter",
        keywords=("openrouter",),
        env_key="OPENROUTER_API_KEY",
        display_name="OpenRouter",
        litellm_prefix="openrouter",        # claude-3 → openrouter/claude-3
        skip_prefixes=(),
        env_extras=(),
        is_gateway=True,
        is_local=False,
        detect_by_key_prefix="sk-or-",
        detect_by_base_keyword="openrouter",
        default_api_base="https://openrouter.ai/api/v1",
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # AiHubMix：全局网关，OpenAI 兼容接口。
    # strip_model_prefix=True：它不理解 "anthropic/claude-3"，
    # 所以我们剥离为裸的 "claude-3"，然后重新添加前缀为 "openai/claude-3"。
    ProviderSpec(
        name="aihubmix",
        keywords=("aihubmix",),
        env_key="OPENAI_API_KEY",           # OpenAI-compatible
        display_name="AiHubMix",
        litellm_prefix="openai",            # → openai/{model}
        skip_prefixes=(),
        env_extras=(),
        is_gateway=True,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="aihubmix",
        default_api_base="https://aihubmix.com/v1",
        strip_model_prefix=True,            # anthropic/claude-3 → claude-3 → openai/claude-3
        model_overrides=(),
    ),

    # === 标准提供商（通过模型名称关键字匹配）==============

    # Anthropic：LiteLLM 原生识别 "claude-*"，无需前缀。
    ProviderSpec(
        name="anthropic",
        keywords=("anthropic", "claude"),
        env_key="ANTHROPIC_API_KEY",
        display_name="Anthropic",
        litellm_prefix="",
        skip_prefixes=(),
        env_extras=(),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # OpenAI：LiteLLM 原生识别 "gpt-*"，无需前缀。
    ProviderSpec(
        name="openai",
        keywords=("openai", "gpt"),
        env_key="OPENAI_API_KEY",
        display_name="OpenAI",
        litellm_prefix="",
        skip_prefixes=(),
        env_extras=(),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # DeepSeek：需要 "deepseek/" 前缀用于 LiteLLM 路由。
    ProviderSpec(
        name="deepseek",
        keywords=("deepseek",),
        env_key="DEEPSEEK_API_KEY",
        display_name="DeepSeek",
        litellm_prefix="deepseek",          # deepseek-chat → deepseek/deepseek-chat
        skip_prefixes=("deepseek/",),       # avoid double-prefix
        env_extras=(),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # Gemini：需要 "gemini/" 前缀用于 LiteLLM。
    ProviderSpec(
        name="gemini",
        keywords=("gemini",),
        env_key="GEMINI_API_KEY",
        display_name="Gemini",
        litellm_prefix="gemini",            # gemini-pro → gemini/gemini-pro
        skip_prefixes=("gemini/",),         # avoid double-prefix
        env_extras=(),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # Zhipu：LiteLLM 使用 "zai/" 前缀。
    # 同时将密钥镜像到 ZHIPUAI_API_KEY（某些 LiteLLM 路径会检查该变量）。
    # skip_prefixes：当已经通过网关路由时，不要添加 "zai/"。
    ProviderSpec(
        name="zhipu",
        keywords=("zhipu", "glm", "zai"),
        env_key="ZAI_API_KEY",
        display_name="Zhipu AI",
        litellm_prefix="zai",              # glm-4 → zai/glm-4
        skip_prefixes=("zhipu/", "zai/", "openrouter/", "hosted_vllm/"),
        env_extras=(
            ("ZHIPUAI_API_KEY", "{api_key}"),
        ),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # DashScope：Qwen 模型，需要 "dashscope/" 前缀。
    ProviderSpec(
        name="dashscope",
        keywords=("qwen", "dashscope"),
        env_key="DASHSCOPE_API_KEY",
        display_name="DashScope",
        litellm_prefix="dashscope",         # qwen-max → dashscope/qwen-max
        skip_prefixes=("dashscope/", "openrouter/"),
        env_extras=(),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # Moonshot：Kimi 模型，需要 "moonshot/" 前缀。
    # LiteLLM 需要 MOONSHOT_API_BASE 环境变量来查找端点。
    # Kimi K2.5 API 强制要求 temperature >= 1.0。
    ProviderSpec(
        name="moonshot",
        keywords=("moonshot", "kimi"),
        env_key="MOONSHOT_API_KEY",
        display_name="Moonshot",
        litellm_prefix="moonshot",          # kimi-k2.5 → moonshot/kimi-k2.5
        skip_prefixes=("moonshot/", "openrouter/"),
        env_extras=(
            ("MOONSHOT_API_BASE", "{api_base}"),
        ),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="https://api.moonshot.ai/v1",   # 国际版；中国使用 api.moonshot.cn
        strip_model_prefix=False,
        model_overrides=(
            ("kimi-k2.5", {"temperature": 1.0}),
        ),
    ),

    # === 本地部署（回退：未知的 api_base → 假设为本地）=====

    # vLLM / 任何 OpenAI 兼容的本地服务器。
    # 如果设置了 api_base 但不匹配已知的网关，我们会落在这里。
    # 放在 Groq 之前，这样当两者都配置时，vLLM 会赢得回退。
    ProviderSpec(
        name="vllm",
        keywords=("vllm",),
        env_key="HOSTED_VLLM_API_KEY",
        display_name="vLLM/Local",
        litellm_prefix="hosted_vllm",      # Llama-3-8B → hosted_vllm/Llama-3-8B
        skip_prefixes=(),
        env_extras=(),
        is_gateway=False,
        is_local=True,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",                # user must provide in config
        strip_model_prefix=False,
        model_overrides=(),
    ),

    # === 辅助（不是主要的 LLM 提供商）============================

    # Groq：主要用于 Whisper 语音转录，也可用于 LLM。
    # 需要 "groq/" 前缀用于 LiteLLM 路由。放在最后 — 它很少赢得回退。
    ProviderSpec(
        name="groq",
        keywords=("groq",),
        env_key="GROQ_API_KEY",
        display_name="Groq",
        litellm_prefix="groq",              # llama3-8b-8192 → groq/llama3-8b-8192
        skip_prefixes=("groq/",),           # avoid double-prefix
        env_extras=(),
        is_gateway=False,
        is_local=False,
        detect_by_key_prefix="",
        detect_by_base_keyword="",
        default_api_base="",
        strip_model_prefix=False,
        model_overrides=(),
    ),
)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def find_by_model(model: str) -> ProviderSpec | None:
    """通过模型名称关键字匹配标准提供商（不区分大小写）。
    跳过网关/本地 — 这些通过 api_key/api_base 匹配。"""
    model_lower = model.lower()
    for spec in PROVIDERS:
        if spec.is_gateway or spec.is_local:
            continue
        if any(kw in model_lower for kw in spec.keywords):
            return spec
    return None


def find_gateway(api_key: str | None, api_base: str | None) -> ProviderSpec | None:
    """通过 api_key 前缀或 api_base 子字符串检测网关/本地。
    回退：未知的 api_base → 视为本地（vLLM）。"""
    for spec in PROVIDERS:
        if spec.detect_by_key_prefix and api_key and api_key.startswith(spec.detect_by_key_prefix):
            return spec
        if spec.detect_by_base_keyword and api_base and spec.detect_by_base_keyword in api_base:
            return spec
    if api_base:
        return next((s for s in PROVIDERS if s.is_local), None)
    return None


def find_by_name(name: str) -> ProviderSpec | None:
    """通过配置字段名查找提供商规范，例如 "dashscope"。"""
    for spec in PROVIDERS:
        if spec.name == name:
            return spec
    return None
