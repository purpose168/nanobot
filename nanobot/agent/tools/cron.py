"""用于调度提醒和任务的 Cron 工具。"""

from typing import Any

from nanobot.agent.tools.base import Tool
from nanobot.cron.service import CronService
from nanobot.cron.types import CronSchedule


class CronTool(Tool):
    """用于调度提醒和周期性任务的工具。"""
    
    def __init__(self, cron_service: CronService):
        self._cron = cron_service
        self._channel = ""
        self._chat_id = ""
    
    def set_context(self, channel: str, chat_id: str) -> None:
        """设置用于投递的当前会话上下文。"""
        self._channel = channel
        self._chat_id = chat_id
    
    @property
    def name(self) -> str:
        return "cron"
    
    @property
    def description(self) -> str:
        return "调度提醒和周期性任务。操作：add、list、remove。"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "list", "remove"],
                    "description": "要执行的操作"
                },
                "message": {
                    "type": "string",
                    "description": "提醒消息（用于 add）"
                },
                "every_seconds": {
                    "type": "integer",
                    "description": "间隔秒数（用于周期性任务）"
                },
                "cron_expr": {
                    "type": "string",
                    "description": "Cron 表达式，如 '0 9 * * *'（用于调度任务）"
                },
                "job_id": {
                    "type": "string",
                    "description": "任务 ID（用于 remove）"
                }
            },
            "required": ["action"]
        }
    
    async def execute(
        self,
        action: str,
        message: str = "",
        every_seconds: int | None = None,
        cron_expr: str | None = None,
        job_id: str | None = None,
        **kwargs: Any
    ) -> str:
        if action == "add":
            return self._add_job(message, every_seconds, cron_expr)
        elif action == "list":
            return self._list_jobs()
        elif action == "remove":
            return self._remove_job(job_id)
        return f"Unknown action: {action}"
    
    def _add_job(self, message: str, every_seconds: int | None, cron_expr: str | None) -> str:
        if not message:
            return "错误：add 操作需要 message 参数"
        if not self._channel or not self._chat_id:
            return "错误：没有会话上下文（channel/chat_id）"
        
        # 构建调度
        if every_seconds:
            schedule = CronSchedule(kind="every", every_ms=every_seconds * 1000)
        elif cron_expr:
            schedule = CronSchedule(kind="cron", expr=cron_expr)
        else:
            return "错误：需要 every_seconds 或 cron_expr 参数"
        
        job = self._cron.add_job(
            name=message[:30],
            schedule=schedule,
            message=message,
            deliver=True,
            channel=self._channel,
            to=self._chat_id,
        )
        return f"Created job '{job.name}' (id: {job.id})"
    
    def _list_jobs(self) -> str:
        jobs = self._cron.list_jobs()
        if not jobs:
            return "没有已调度的任务。"
        lines = [f"- {j.name} (id: {j.id}, {j.schedule.kind})" for j in jobs]
        return "已调度的任务：\n" + "\n".join(lines)
    
    def _remove_job(self, job_id: str | None) -> str:
        if not job_id:
            return "错误：remove 操作需要 job_id 参数"
        if self._cron.remove_job(job_id):
            return f"已移除任务 {job_id}"
        return f"未找到任务 {job_id}"
