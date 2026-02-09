"""使用 python-telegram-bot 的 Telegram 通道实现。"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING

from loguru import logger
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import TelegramConfig

if TYPE_CHECKING:
    from nanobot.session.manager import SessionManager


def _markdown_to_telegram_html(text: str) -> str:
    """
    将 markdown 转换为 Telegram 安全的 HTML。
    """
    if not text:
        return ""
    
    # 1. 提取并保护代码块（保留内容免受其他处理影响）
    code_blocks: list[str] = []
    def save_code_block(m: re.Match) -> str:
        code_blocks.append(m.group(1))
        return f"\x00CB{len(code_blocks) - 1}\x00"
    
    text = re.sub(r'```[\w]*\n?([\s\S]*?)```', save_code_block, text)
    
    # 2. 提取并保护内联代码
    inline_codes: list[str] = []
    def save_inline_code(m: re.Match) -> str:
        inline_codes.append(m.group(1))
        return f"\x00IC{len(inline_codes) - 1}\x00"
    
    text = re.sub(r'`([^`]+)`', save_inline_code, text)
    
    # 3. 标题 # Title -> 仅标题文本
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # 4. 引用块 > text -> 仅文本（在 HTML 转义之前）
    text = re.sub(r'^>\s*(.*)$', r'\1', text, flags=re.MULTILINE)
    
    # 5. 转义 HTML 特殊字符
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 6. 链接 [text](url) - 必须在粗体/斜体之前以处理嵌套情况
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # 7. 粗体 **text** 或 __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    
    # 8. 斜体 _text_（避免匹配单词内部，如 some_var_name）
    text = re.sub(r'(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])', r'<i>\1</i>', text)
    
    # 9. 删除线 ~~text~~
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    
    # 10. 项目符号列表 - item -> • item
    text = re.sub(r'^[-*]\s+', '• ', text, flags=re.MULTILINE)
    
    # 11. 使用 HTML 标签恢复内联代码
    for i, code in enumerate(inline_codes):
        # Escape HTML in code content
        escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace(f"\x00IC{i}\x00", f"<code>{escaped}</code>")
    
    # 12. 使用 HTML 标签恢复代码块
    for i, code in enumerate(code_blocks):
        # 转义代码内容中的 HTML
        escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace(f"\x00CB{i}\x00", f"<pre><code>{escaped}</code></pre>")
    
    return text


class TelegramChannel(BaseChannel):
    """
    使用长轮询的 Telegram 通道。
    
    简单可靠 - 不需要 webhook/公网 IP。
    """
    
    name = "telegram"
    
    # 在 Telegram 命令菜单中注册的命令
    BOT_COMMANDS = [
        BotCommand("start", "启动机器人"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("help", "显示可用命令"),
    ]
    
    def __init__(
        self,
        config: TelegramConfig,
        bus: MessageBus,
        groq_api_key: str = "",
        session_manager: SessionManager | None = None,
    ):
        super().__init__(config, bus)
        self.config: TelegramConfig = config
        self.groq_api_key = groq_api_key
        self.session_manager = session_manager
        self._app: Application | None = None
        self._chat_ids: dict[str, int] = {}  # 将 sender_id 映射到 chat_id 以便回复
        self._typing_tasks: dict[str, asyncio.Task] = {}  # chat_id -> 输入循环任务
    
    async def start(self) -> None:
        """使用长轮询启动 Telegram 机器人。"""
        if not self.config.token:
            logger.error("未配置 Telegram bot 令牌")
            return
        
        self._running = True
        
        # 构建应用程序
        builder = Application.builder().token(self.config.token)
        if self.config.proxy:
            builder = builder.proxy(self.config.proxy).get_updates_proxy(self.config.proxy)
        self._app = builder.build()
        
        # 添加命令处理器
        self._app.add_handler(CommandHandler("start", self._on_start))
        self._app.add_handler(CommandHandler("reset", self._on_reset))
        self._app.add_handler(CommandHandler("help", self._on_help))
        
        # 添加消息处理器用于文本、照片、语音、文档
        self._app.add_handler(
            MessageHandler(
                (filters.TEXT | filters.PHOTO | filters.VOICE | filters.AUDIO | filters.Document.ALL) 
                & ~filters.COMMAND, 
                self._on_message
            )
        )
        
        logger.info("正在启动 Telegram 机器人（轮询模式）...")
        
        # 初始化并启动轮询
        await self._app.initialize()
        await self._app.start()
        
        # 获取机器人信息并注册命令菜单
        bot_info = await self._app.bot.get_me()
        logger.info(f"Telegram 机器人 @{bot_info.username} 已连接")
        
        try:
            await self._app.bot.set_my_commands(self.BOT_COMMANDS)
            logger.debug("Telegram 机器人命令已注册")
        except Exception as e:
            logger.warning(f"注册机器人命令失败：{e}")
        
        # 启动轮询（运行直到停止）
        await self._app.updater.start_polling(
            allowed_updates=["message"],
            drop_pending_updates=True  # 启动时忽略旧消息
        )
        
        # 保持运行直到停止
        while self._running:
            await asyncio.sleep(1)
    
    async def stop(self) -> None:
        """停止 Telegram 机器人。"""
        self._running = False
        
        # 取消所有输入指示器
        for chat_id in list(self._typing_tasks):
            self._stop_typing(chat_id)
        
        if self._app:
            logger.info("正在停止 Telegram 机器人...")
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
            self._app = None
    
    async def send(self, msg: OutboundMessage) -> None:
        """通过 Telegram 发送消息。"""
        if not self._app:
            logger.warning("Telegram 机器人未运行")
            return
        
        # 停止此聊天的输入指示器
        self._stop_typing(msg.chat_id)
        
        try:
            # chat_id 应该是 Telegram 聊天 ID（整数）
            chat_id = int(msg.chat_id)
            # 将 markdown 转换为 Telegram HTML
            html_content = _markdown_to_telegram_html(msg.content)
            await self._app.bot.send_message(
                chat_id=chat_id,
                text=html_content,
                parse_mode="HTML"
            )
        except ValueError:
            logger.error(f"无效的 chat_id：{msg.chat_id}")
        except Exception as e:
            # 如果 HTML 解析失败，则回退到纯文本
            logger.warning(f"HTML 解析失败，回退到纯文本：{e}")
            try:
                await self._app.bot.send_message(
                    chat_id=int(msg.chat_id),
                    text=msg.content
                )
            except Exception as e2:
                logger.error(f"发送 Telegram 消息时出错：{e2}")
    
    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /start 命令。"""
        if not update.message or not update.effective_user:
            return
        
        user = update.effective_user
        await update.message.reply_text(
            f"👋 你好 {user.first_name}！我是 nanobot。\n\n"
            "给我发一条消息，我会回复！\n"
            "输入 /help 查看可用命令。"
        )
    
    async def _on_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /reset 命令 — 清除对话历史。"""
        if not update.message or not update.effective_user:
            return
        
        chat_id = str(update.message.chat_id)
        session_key = f"{self.name}:{chat_id}"
        
        if self.session_manager is None:
            logger.warning("/reset 被调用，但 session_manager 不可用")
            await update.message.reply_text("⚠️ 会话管理不可用。")
            return
        
        session = self.session_manager.get_or_create(session_key)
        msg_count = len(session.messages)
        session.clear()
        self.session_manager.save(session)
        
        logger.info(f"会话重置 {session_key}（清除了 {msg_count} 条消息）")
        await update.message.reply_text("🔄 对话历史已清除。让我们重新开始！")
    
    async def _on_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /help 命令 — 显示可用命令。"""
        if not update.message:
            return
        
        help_text = (
            "🐈 <b>nanobot 命令</b>\n\n"
            "/start — 启动机器人\n"
            "/reset — 重置对话历史\n"
            "/help — 显示此帮助消息\n\n"
            "给我发一条文本消息即可聊天！"
        )
        await update.message.reply_text(help_text, parse_mode="HTML")
    
    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理传入消息（文本、照片、语音、文档）。"""
        if not update.message or not update.effective_user:
            return
        
        message = update.message
        user = update.effective_user
        chat_id = message.chat_id
        
        # 使用稳定的数字 ID，但保留用户名以便白名单兼容
        sender_id = str(user.id)
        if user.username:
            sender_id = f"{sender_id}|{user.username}"
        
        # 存储聊天 ID 以便回复
        self._chat_ids[sender_id] = chat_id
        
        # 从文本和/或媒体构建内容
        content_parts = []
        media_paths = []
        
        # 文本内容
        if message.text:
            content_parts.append(message.text)
        if message.caption:
            content_parts.append(message.caption)
        
        # 处理媒体文件
        media_file = None
        media_type = None
        
        if message.photo:
            media_file = message.photo[-1]  # 最大的照片
            media_type = "image"
        elif message.voice:
            media_file = message.voice
            media_type = "voice"
        elif message.audio:
            media_file = message.audio
            media_type = "audio"
        elif message.document:
            media_file = message.document
            media_type = "file"
        
        # 如果存在媒体，则下载
        if media_file and self._app:
            try:
                file = await self._app.bot.get_file(media_file.file_id)
                ext = self._get_extension(media_type, getattr(media_file, 'mime_type', None))
                
                # 保存到 workspace/media/
                from pathlib import Path
                media_dir = Path.home() / ".nanobot" / "media"
                media_dir.mkdir(parents=True, exist_ok=True)
                
                file_path = media_dir / f"{media_file.file_id[:16]}{ext}"
                await file.download_to_drive(str(file_path))
                
                media_paths.append(str(file_path))
                
                # 处理语音转录
                if media_type == "voice" or media_type == "audio":
                    from nanobot.providers.transcription import GroqTranscriptionProvider
                    transcriber = GroqTranscriptionProvider(api_key=self.groq_api_key)
                    transcription = await transcriber.transcribe(file_path)
                    if transcription:
                        logger.info(f"已转录 {media_type}：{transcription[:50]}...")
                        content_parts.append(f"[转录：{transcription}]")
                    else:
                        content_parts.append(f"[{media_type}: {file_path}]")
                else:
                    content_parts.append(f"[{media_type}: {file_path}]")
                    
                logger.debug(f"已下载 {media_type} 到 {file_path}")
            except Exception as e:
                logger.error(f"下载媒体失败：{e}")
                content_parts.append(f"[{media_type}: 下载失败]")
        
        content = "\n".join(content_parts) if content_parts else "[空消息]"
        
        logger.debug(f"来自 {sender_id} 的 Telegram 消息：{content[:50]}...")
        
        str_chat_id = str(chat_id)
        
        # 在处理之前启动输入指示器
        self._start_typing(str_chat_id)
        
        # 转发到消息总线
        await self._handle_message(
            sender_id=sender_id,
            chat_id=str_chat_id,
            content=content,
            media=media_paths,
            metadata={
                "message_id": message.message_id,
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "is_group": message.chat.type != "private"
            }
        )
    
    def _start_typing(self, chat_id: str) -> None:
        """开始为聊天发送'正在输入...'指示器。"""
        # 取消此聊天的任何现有输入任务
        self._stop_typing(chat_id)
        self._typing_tasks[chat_id] = asyncio.create_task(self._typing_loop(chat_id))
    
    def _stop_typing(self, chat_id: str) -> None:
        """停止聊天的输入指示器。"""
        task = self._typing_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()
    
    async def _typing_loop(self, chat_id: str) -> None:
        """重复发送'正在输入'操作直到取消。"""
        try:
            while self._app:
                await self._app.bot.send_chat_action(chat_id=int(chat_id), action="typing")
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"输入指示器停止 {chat_id}：{e}")
    
    def _get_extension(self, media_type: str, mime_type: str | None) -> str:
        """根据媒体类型获取文件扩展名。"""
        if mime_type:
            ext_map = {
                "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
                "audio/ogg": ".ogg", "audio/mpeg": ".mp3", "audio/mp4": ".m4a",
            }
            if mime_type in ext_map:
                return ext_map[mime_type]
        
        type_map = {"image": ".jpg", "voice": ".ogg", "audio": ".mp3", "file": ""}
        return type_map.get(media_type, "")
