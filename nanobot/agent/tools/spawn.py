"""用于创建后台子智能体的生成工具。"""

from typing import Any, TYPE_CHECKING

from nanobot.agent.tools.base import Tool

if TYPE_CHECKING:
    from nanobot.agent.subagent import SubagentManager


class SpawnTool(Tool):
    """
    用于生成子智能体以执行后台任务的工具。
    
    子智能体异步运行，并在完成时将结果
    通知回主智能体。
    """
    
    def __init__(self, manager: "SubagentManager"):
        self._manager = manager
        self._origin_channel = "cli"
        self._origin_chat_id = "direct"
    
    def set_context(self, channel: str, chat_id: str) -> None:
        """设置子智能体通知的源上下文。"""
        self._origin_channel = channel
        self._origin_chat_id = chat_id
    
    @property
    def name(self) -> str:
        return "spawn"
    
    @property
    def description(self) -> str:
        return (
            "生成一个子智能体来在后台处理任务。"
            "用于可以独立运行的复杂或耗时任务。"
            "子智能体将完成任务并在完成后报告。"
        )
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "子智能体要完成的任务",
                },
                "label": {
                    "type": "string",
                    "description": "任务的可选简短标签（用于显示）",
                },
            },
            "required": ["task"],
        }
    
    async def execute(self, task: str, label: str | None = None, **kwargs: Any) -> str:
        """生成一个子智能体来执行给定的任务。"""
        return await self._manager.spawn(
            task=task,
            label=label,
            origin_channel=self._origin_channel,
            origin_chat_id=self._origin_chat_id,
        )
