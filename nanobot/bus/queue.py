"""用于解耦通道-智能体通信的异步消息队列。"""

import asyncio
from typing import Callable, Awaitable

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """
    将聊天通道与智能体核心解耦的异步消息总线。
    
    通道将消息推送到入站队列，智能体处理它们
    并将响应推送到出站队列。
    """
    
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        self._outbound_subscribers: dict[str, list[Callable[[OutboundMessage], Awaitable[None]]]] = {}
        self._running = False
    
    async def publish_inbound(self, msg: InboundMessage) -> None:
        """从通道向智能体发布消息。"""
        await self.inbound.put(msg)
    
    async def consume_inbound(self) -> InboundMessage:
        """消费下一条入站消息（阻塞直到可用）。"""
        return await self.inbound.get()
    
    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """从智能体向通道发布响应。"""
        await self.outbound.put(msg)
    
    async def consume_outbound(self) -> OutboundMessage:
        """消费下一条出站消息（阻塞直到可用）。"""
        return await self.outbound.get()
    
    def subscribe_outbound(
        self, 
        channel: str, 
        callback: Callable[[OutboundMessage], Awaitable[None]]
    ) -> None:
        """订阅特定通道的出站消息。"""
        if channel not in self._outbound_subscribers:
            self._outbound_subscribers[channel] = []
        self._outbound_subscribers[channel].append(callback)
    
    async def dispatch_outbound(self) -> None:
        """
        将出站消息分发到订阅的通道。
        将此作为后台任务运行。
        """
        self._running = True
        while self._running:
            try:
                msg = await asyncio.wait_for(self.outbound.get(), timeout=1.0)
                subscribers = self._outbound_subscribers.get(msg.channel, [])
                for callback in subscribers:
                    try:
                        await callback(msg)
                    except Exception as e:
                        logger.error(f"分发到 {msg.channel} 时出错：{e}")
            except asyncio.TimeoutError:
                continue
    
    def stop(self) -> None:
        """停止分发器循环。"""
        self._running = False
    
    @property
    def inbound_size(self) -> int:
        """待处理的入站消息数量。"""
        return self.inbound.qsize()
    
    @property
    def outbound_size(self) -> int:
        """待处理的出站消息数量。"""
        return self.outbound.qsize()
