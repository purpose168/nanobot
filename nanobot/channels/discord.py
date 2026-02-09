"""使用 Discord Gateway websocket 的 Discord 通道实现。"""

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import websockets
from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import DiscordConfig


DISCORD_API_BASE = "https://discord.com/api/v10"
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024  # 20MB


class DiscordChannel(BaseChannel):
    """使用 Gateway websocket 的 Discord 通道。"""

    name = "discord"

    def __init__(self, config: DiscordConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: DiscordConfig = config
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._seq: int | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._typing_tasks: dict[str, asyncio.Task] = {}
        self._http: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """启动 Discord 网关连接。"""
        if not self.config.token:
            logger.error("未配置 Discord bot 令牌")
            return

        self._running = True
        self._http = httpx.AsyncClient(timeout=30.0)

        while self._running:
            try:
                logger.info("正在连接到 Discord 网关...")
                async with websockets.connect(self.config.gateway_url) as ws:
                    self._ws = ws
                    await self._gateway_loop()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Discord 网关错误：{e}")
                if self._running:
                    logger.info("5 秒后重新连接到 Discord 网关...")
                    await asyncio.sleep(5)

    async def stop(self) -> None:
        """停止 Discord 通道。"""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        for task in self._typing_tasks.values():
            task.cancel()
        self._typing_tasks.clear()
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._http:
            await self._http.aclose()
            self._http = None

    async def send(self, msg: OutboundMessage) -> None:
        """通过 Discord REST API 发送消息。"""
        if not self._http:
            logger.warning("Discord HTTP 客户端未初始化")
            return

        url = f"{DISCORD_API_BASE}/channels/{msg.chat_id}/messages"
        payload: dict[str, Any] = {"content": msg.content}

        if msg.reply_to:
            payload["message_reference"] = {"message_id": msg.reply_to}
            payload["allowed_mentions"] = {"replied_user": False}

        headers = {"Authorization": f"Bot {self.config.token}"}

        try:
            for attempt in range(3):
                try:
                    response = await self._http.post(url, headers=headers, json=payload)
                    if response.status_code == 429:
                        data = response.json()
                        retry_after = float(data.get("retry_after", 1.0))
                        logger.warning(f"Discord 速率受限，{retry_after}秒后重试")
                        await asyncio.sleep(retry_after)
                        continue
                    response.raise_for_status()
                    return
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"发送 Discord 消息时出错：{e}")
                    else:
                        await asyncio.sleep(1)
        finally:
            await self._stop_typing(msg.chat_id)

    async def _gateway_loop(self) -> None:
        """主网关循环：识别、心跳、分发事件。"""
        if not self._ws:
            return

        async for raw in self._ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(f"来自 Discord 网关的无效 JSON：{raw[:100]}")
                continue

            op = data.get("op")
            event_type = data.get("t")
            seq = data.get("s")
            payload = data.get("d")

            if seq is not None:
                self._seq = seq

            if op == 10:
                # HELLO: 启动心跳和识别
                interval_ms = payload.get("heartbeat_interval", 45000)
                await self._start_heartbeat(interval_ms / 1000)
                await self._identify()
            elif op == 0 and event_type == "READY":
                logger.info("Discord 网关就绪")
            elif op == 0 and event_type == "MESSAGE_CREATE":
                await self._handle_message_create(payload)
            elif op == 7:
                # RECONNECT: 退出循环以重新连接
                logger.info("Discord 网关请求重新连接")
                break
            elif op == 9:
                # INVALID_SESSION: 重新连接
                logger.warning("Discord 网关会话无效")
                break

    async def _identify(self) -> None:
        """发送 IDENTIFY 负载。"""
        if not self._ws:
            return

        identify = {
            "op": 2,
            "d": {
                "token": self.config.token,
                "intents": self.config.intents,
                "properties": {
                    "os": "nanobot",
                    "browser": "nanobot",
                    "device": "nanobot",
                },
            },
        }
        await self._ws.send(json.dumps(identify))

    async def _start_heartbeat(self, interval_s: float) -> None:
        """启动或重启心跳循环。"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        async def heartbeat_loop() -> None:
            while self._running and self._ws:
                payload = {"op": 1, "d": self._seq}
                try:
                    await self._ws.send(json.dumps(payload))
                except Exception as e:
                    logger.warning(f"Discord 心跳失败：{e}")
                    break
                await asyncio.sleep(interval_s)

        self._heartbeat_task = asyncio.create_task(heartbeat_loop())

    async def _handle_message_create(self, payload: dict[str, Any]) -> None:
        """处理传入的 Discord 消息。"""
        author = payload.get("author") or {}
        if author.get("bot"):
            return

        sender_id = str(author.get("id", ""))
        channel_id = str(payload.get("channel_id", ""))
        content = payload.get("content") or ""

        if not sender_id or not channel_id:
            return

        if not self.is_allowed(sender_id):
            return

        content_parts = [content] if content else []
        media_paths: list[str] = []
        media_dir = Path.home() / ".nanobot" / "media"

        for attachment in payload.get("attachments") or []:
            url = attachment.get("url")
            filename = attachment.get("filename") or "attachment"
            size = attachment.get("size") or 0
            if not url or not self._http:
                continue
            if size and size > MAX_ATTACHMENT_BYTES:
                content_parts.append(f"[附件：{filename} - 太大]")
                continue
            try:
                media_dir.mkdir(parents=True, exist_ok=True)
                file_path = media_dir / f"{attachment.get('id', 'file')}_{filename.replace('/', '_')}"
                resp = await self._http.get(url)
                resp.raise_for_status()
                file_path.write_bytes(resp.content)
                media_paths.append(str(file_path))
                content_parts.append(f"[附件：{file_path}]")
            except Exception as e:
                logger.warning(f"下载 Discord 附件失败：{e}")
                content_parts.append(f"[附件：{filename} - 下载失败]")

        reply_to = (payload.get("referenced_message") or {}).get("id")

        await self._start_typing(channel_id)

        await self._handle_message(
            sender_id=sender_id,
            chat_id=channel_id,
            content="\n".join(p for p in content_parts if p) or "[空消息]",
            media=media_paths,
            metadata={
                "message_id": str(payload.get("id", "")),
                "guild_id": payload.get("guild_id"),
                "reply_to": reply_to,
            },
        )

    async def _start_typing(self, channel_id: str) -> None:
        """为通道启动周期性输入指示器。"""
        await self._stop_typing(channel_id)

        async def typing_loop() -> None:
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/typing"
            headers = {"Authorization": f"Bot {self.config.token}"}
            while self._running:
                try:
                    await self._http.post(url, headers=headers)
                except Exception:
                    pass
                await asyncio.sleep(8)

        self._typing_tasks[channel_id] = asyncio.create_task(typing_loop())

    async def _stop_typing(self, channel_id: str) -> None:
        """停止通道的输入指示器。"""
        task = self._typing_tasks.pop(channel_id, None)
        if task:
            task.cancel()
