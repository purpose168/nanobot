"""用于后台任务执行的子智能体管理器。"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, ListDirTool
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.web import WebSearchTool, WebFetchTool


class SubagentManager:
    """
    管理后台子智能体的执行。
    
    子智能体是轻量级的智能体实例，在后台运行
    以处理特定任务。它们共享相同的 LLM 提供商，但具有
    隔离的上下文和专注的系统提示。
    """
    
    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        bus: MessageBus,
        model: str | None = None,
        brave_api_key: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
        restrict_to_workspace: bool = False,
    ):
        from nanobot.config.schema import ExecToolConfig
        self.provider = provider
        self.workspace = workspace
        self.bus = bus
        self.model = model or provider.get_default_model()
        self.brave_api_key = brave_api_key
        self.exec_config = exec_config or ExecToolConfig()
        self.restrict_to_workspace = restrict_to_workspace
        self._running_tasks: dict[str, asyncio.Task[None]] = {}
    
    async def spawn(
        self,
        task: str,
        label: str | None = None,
        origin_channel: str = "cli",
        origin_chat_id: str = "direct",
    ) -> str:
        """
        生成一个子智能体来在后台执行任务。
        
        参数:
            task: 子智能体的任务描述。
            label: 任务的可选人类可读标签。
            origin_channel: 要将结果通知到的通道。
            origin_chat_id: 要将结果通知到的聊天 ID。
        
        返回:
            指示子智能体已启动的状态消息。
        """
        task_id = str(uuid.uuid4())[:8]
        display_label = label or task[:30] + ("..." if len(task) > 30 else "")
        
        origin = {
            "channel": origin_channel,
            "chat_id": origin_chat_id,
        }
        
        # 创建后台任务
        bg_task = asyncio.create_task(
            self._run_subagent(task_id, task, display_label, origin)
        )
        self._running_tasks[task_id] = bg_task
        
        # 完成时清理
        bg_task.add_done_callback(lambda _: self._running_tasks.pop(task_id, None))
        
        logger.info(f"已生成子智能体 [{task_id}]: {display_label}")
        return f"子智能体 [{display_label}] 已启动（id：{task_id}）。完成后我会通知您。"
    
    async def _run_subagent(
        self,
        task_id: str,
        task: str,
        label: str,
        origin: dict[str, str],
    ) -> None:
        """执行子智能体任务并通知结果。"""
        logger.info(f"子智能体 [{task_id}] 正在启动任务：{label}")
        
        try:
            # 构建子智能体工具（无消息工具，无生成工具）
            tools = ToolRegistry()
            allowed_dir = self.workspace if self.restrict_to_workspace else None
            tools.register(ReadFileTool(allowed_dir=allowed_dir))
            tools.register(WriteFileTool(allowed_dir=allowed_dir))
            tools.register(ListDirTool(allowed_dir=allowed_dir))
            tools.register(ExecTool(
                working_dir=str(self.workspace),
                timeout=self.exec_config.timeout,
                restrict_to_workspace=self.restrict_to_workspace,
            ))
            tools.register(WebSearchTool(api_key=self.brave_api_key))
            tools.register(WebFetchTool())
            
            # 使用子智能体特定的提示构建消息
            system_prompt = self._build_subagent_prompt(task)
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]
            
            # 运行智能体循环（限制迭代次数）
            max_iterations = 15
            iteration = 0
            final_result: str | None = None
            
            while iteration < max_iterations:
                iteration += 1
                
                response = await self.provider.chat(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=self.model,
                )
                
                if response.has_tool_calls:
                    # 添加带有工具调用的助手消息
                    tool_call_dicts = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in response.tool_calls
                    ]
                    messages.append({
                        "role": "assistant",
                        "content": response.content or "",
                        "tool_calls": tool_call_dicts,
                    })
                    
                    # 执行工具
                    for tool_call in response.tool_calls:
                        args_str = json.dumps(tool_call.arguments)
                        logger.debug(f"子智能体 [{task_id}] 正在执行：{tool_call.name} 参数：{args_str}")
                        result = await tools.execute(tool_call.name, tool_call.arguments)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.name,
                            "content": result,
                        })
                else:
                    final_result = response.content
                    break
            
            if final_result is None:
                final_result = "任务已完成但未生成最终响应。"
            
            logger.info(f"子智能体 [{task_id}] 成功完成")
            await self._announce_result(task_id, label, task, final_result, origin, "ok")
            
        except Exception as e:
            error_msg = f"错误：{str(e)}"
            logger.error(f"子智能体 [{task_id}] 失败：{e}")
            await self._announce_result(task_id, label, task, error_msg, origin, "error")
    
    async def _announce_result(
        self,
        task_id: str,
        label: str,
        task: str,
        result: str,
        origin: dict[str, str],
        status: str,
    ) -> None:
        """通过消息总线向主智能体通知子智能体结果。"""
        status_text = "成功完成" if status == "ok" else "失败"
        
        announce_content = f"""[子智能体 '{label}' {status_text}]

任务：{task}

结果：
{result}

为用户自然地总结这一点。保持简短（1-2 句话）。不要提及技术细节，如"子智能体"或任务 ID。"""
        
        # 作为系统消息注入以触发主智能体
        msg = InboundMessage(
            channel="system",
            sender_id="subagent",
            chat_id=f"{origin['channel']}:{origin['chat_id']}",
            content=announce_content,
        )
        
        await self.bus.publish_inbound(msg)
        logger.debug(f"子智能体 [{task_id}] 已将结果通知到 {origin['channel']}:{origin['chat_id']}")
    
    def _build_subagent_prompt(self, task: str) -> str:
        """为子智能体构建专注的系统提示。"""
        return f"""# 子智能体

你是主智能体生成的子智能体，用于完成特定任务。

## 你的任务
{task}

## 规则
1. 保持专注 —— 只完成分配的任务，不做其他事情
2. 你的最终响应将报告回主智能体
3. 不要发起对话或承担其他任务
4. 在你的发现中要简洁但信息丰富

## 你能做什么
- 在工作区中读取和写入文件
- 执行 shell 命令
- 搜索网络和获取网页
- 彻底完成任务

## 你不能做什么
- 直接向用户发送消息（没有可用的消息工具）
- 生成其他子智能体
- 访问主智能体的对话历史

## 工作区
你的工作区位于：{self.workspace}

当你完成任务时，提供你的发现或操作的清晰总结。"""
    
    def get_running_count(self) -> int:
        """返回当前运行的子智能体数量。"""
        return len(self._running_tasks)
