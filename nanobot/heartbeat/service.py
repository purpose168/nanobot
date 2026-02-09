"""心跳服务 - 定期唤醒智能体以检查任务。"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Coroutine

from loguru import logger

# 默认间隔：30 分钟
DEFAULT_HEARTBEAT_INTERVAL_S = 30 * 60

# 心跳期间发送给智能体的提示
HEARTBEAT_PROMPT = """读取工作空间中的 HEARTBEAT.md（如果存在）。
遵循那里列出的任何说明或任务。
如果不需要关注，只需回复：HEARTBEAT_OK"""

# 表示"无事可做"的令牌
HEARTBEAT_OK_TOKEN = "HEARTBEAT_OK"


def _is_heartbeat_empty(content: str | None) -> bool:
    """检查 HEARTBEAT.md 是否没有可操作的内容。"""
    if not content:
        return True
    
    # 要跳过的行：空行、标题、HTML 注释、空复选框
    skip_patterns = {"- [ ]", "* [ ]", "- [x]", "* [x]"}
    
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("<!--") or line in skip_patterns:
            continue
        return False  # Found actionable content
        # 发现可操作的内容
    
    return True


class HeartbeatService:
    """
    定期心跳服务，唤醒智能体以检查任务。
    
    智能体从工作空间读取 HEARTBEAT.md 并执行
    那里列出的任何任务。如果不需要关注，它回复 HEARTBEAT_OK。
    """
    
    def __init__(
        self,
        workspace: Path,
        on_heartbeat: Callable[[str], Coroutine[Any, Any, str]] | None = None,
        interval_s: int = DEFAULT_HEARTBEAT_INTERVAL_S,
        enabled: bool = True,
    ):
        self.workspace = workspace
        self.on_heartbeat = on_heartbeat
        self.interval_s = interval_s
        self.enabled = enabled
        self._running = False
        self._task: asyncio.Task | None = None
    
    @property
    def heartbeat_file(self) -> Path:
        return self.workspace / "HEARTBEAT.md"
    
    def _read_heartbeat_file(self) -> str | None:
        """读取 HEARTBEAT.md 内容。"""
        if self.heartbeat_file.exists():
            try:
                return self.heartbeat_file.read_text()
            except Exception:
                return None
        return None
    
    async def start(self) -> None:
        """启动心跳服务。"""
        if not self.enabled:
            logger.info("心跳已禁用")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"心跳已启动（每 {self.interval_s} 秒）")
    
    def stop(self) -> None:
        """停止心跳服务。"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
    
    async def _run_loop(self) -> None:
        """主心跳循环。"""
        while self._running:
            try:
                await asyncio.sleep(self.interval_s)
                if self._running:
                    await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳错误：{e}")
    
    async def _tick(self) -> None:
        """执行单个心跳滴答。"""
        content = self._read_heartbeat_file()
        
        # 如果 HEARTBEAT.md 为空或不存在则跳过
        if _is_heartbeat_empty(content):
            logger.debug("心跳：没有任务（HEARTBEAT.md 为空）")
            return
        
        logger.info("心跳：正在检查任务...")
        
        if self.on_heartbeat:
            try:
                response = await self.on_heartbeat(HEARTBEAT_PROMPT)
                
                # 检查智能体是否说"无事可做"
                if HEARTBEAT_OK_TOKEN.replace("_", "") in response.upper().replace("_", ""):
                    logger.info("心跳：OK（无需操作）")
                else:
                    logger.info(f"心跳：已完成任务")
                    
            except Exception as e:
                logger.error(f"心跳执行失败：{e}")
    
    async def trigger_now(self) -> str | None:
        """手动触发心跳。"""
        if self.on_heartbeat:
            return await self.on_heartbeat(HEARTBEAT_PROMPT)
        return None
