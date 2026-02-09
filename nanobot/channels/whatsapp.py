"""使用 Node.js 桥接的 WhatsApp 通道实现。"""

import asyncio
import json
from typing import Any

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import WhatsAppConfig


class WhatsAppChannel(BaseChannel):
    """
    连接到 Node.js 桥接的 WhatsApp 通道。
    
    桥接使用 @whiskeysockets/baileys 来处理 WhatsApp Web 协议。
    Python 和 Node.js 之间的通信通过 WebSocket 进行。
    """
    
    name = "whatsapp"
    
    def __init__(self, config: WhatsAppConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: WhatsAppConfig = config
        self._ws = None
        self._connected = False
    
    async def start(self) -> None:
        """通过连接到桥接启动 WhatsApp 通道。"""
        import websockets
        
        bridge_url = self.config.bridge_url
        
        logger.info(f"正在连接到位于 {bridge_url} 的 WhatsApp 桥接...")
        
        self._running = True
        
        while self._running:
            try:
                async with websockets.connect(bridge_url) as ws:
                    self._ws = ws
                    self._connected = True
                    logger.info("已连接到 WhatsApp 桥接")
                    
                    # 监听消息
                    async for message in ws:
                        try:
                            await self._handle_bridge_message(message)
                        except Exception as e:
                            logger.error(f"处理桥接消息时出错：{e}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._connected = False
                self._ws = None
                logger.warning(f"WhatsApp 桥接连接错误：{e}")
                
                if self._running:
                    logger.info("5 秒后重新连接...")
                    await asyncio.sleep(5)
    
    async def stop(self) -> None:
        """停止 WhatsApp 通道。"""
        self._running = False
        self._connected = False
        
        if self._ws:
            await self._ws.close()
            self._ws = None
    
    async def send(self, msg: OutboundMessage) -> None:
        """通过 WhatsApp 发送消息。"""
        if not self._ws or not self._connected:
            logger.warning("WhatsApp 桥接未连接")
            return
        
        try:
            payload = {
                "type": "send",
                "to": msg.chat_id,
                "text": msg.content
            }
            await self._ws.send(json.dumps(payload))
        except Exception as e:
            logger.error(f"发送 WhatsApp 消息时出错：{e}")
    
    async def _handle_bridge_message(self, raw: str) -> None:
        """处理来自桥接的消息。"""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"来自桥接的无效 JSON：{raw[:100]}")
            return
        
        msg_type = data.get("type")
        
        if msg_type == "message":
            # 来自 WhatsApp 的传入消息
            # WhatsApp 已弃用：旧电话号码样式通常为：<phone>@s.whatspp.net
            pn = data.get("pn", "")
            # 新的 LID 样式通常为：
            sender = data.get("sender", "")
            content = data.get("content", "")
            
            # 仅提取电话号码或 lid 作为 chat_id
            user_id = pn if pn else sender
            sender_id = user_id.split("@")[0] if "@" in user_id else user_id
            logger.info(f"发送者 {sender}")
            
            # 如果是语音消息，则处理语音转录
            if content == "[Voice Message]":
                logger.info(f"收到来自 {sender_id} 的语音消息，但桥接尚不支持直接下载。")
                content = "[语音消息：WhatsApp 尚不支持转录]"
            
            await self._handle_message(
                sender_id=sender_id,
                chat_id=sender,  # 使用完整的 LID 进行回复
                content=content,
                metadata={
                    "message_id": data.get("id"),
                    "timestamp": data.get("timestamp"),
                    "is_group": data.get("isGroup", False)
                }
            )
        
        elif msg_type == "status":
            # 连接状态更新
            status = data.get("status")
            logger.info(f"WhatsApp 状态：{status}")
            
            if status == "connected":
                self._connected = True
            elif status == "disconnected":
                self._connected = False
        
        elif msg_type == "qr":
            # 用于身份验证的 QR 码
            logger.info("在桥接终端中扫描 QR 码以连接 WhatsApp")
        
        elif msg_type == "error":
            logger.error(f"WhatsApp 桥接错误：{data.get('error')}")
