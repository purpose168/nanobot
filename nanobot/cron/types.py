"""Cron 类型。"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class CronSchedule:
    """Cron 作业的调度定义。"""
    kind: Literal["at", "every", "cron"]
    # For "at": timestamp in ms
    # 对于 "at"：毫秒时间戳
    at_ms: int | None = None
    # For "every": interval in ms
    # 对于 "every"：毫秒间隔
    every_ms: int | None = None
    # For "cron": cron expression (e.g. "0 9 * * *")
    # 对于 "cron"：cron 表达式（例如 "0 9 * * *"）
    expr: str | None = None
    # Timezone for cron expressions
    # cron 表达式的时区
    tz: str | None = None


@dataclass
class CronPayload:
    """作业运行时要执行的操作。"""
    kind: Literal["system_event", "agent_turn"] = "agent_turn"
    message: str = ""
    # Deliver response to channel
    # 将响应传递到通道
    deliver: bool = False
    channel: str | None = None  # e.g. "whatsapp"
    # 例如 "whatsapp"
    to: str | None = None  # e.g. phone number
    # 例如电话号码


@dataclass
class CronJobState:
    """作业的运行时状态。"""
    next_run_at_ms: int | None = None
    last_run_at_ms: int | None = None
    last_status: Literal["ok", "error", "skipped"] | None = None
    last_error: str | None = None


@dataclass
class CronJob:
    """一个已调度的作业。"""
    id: str
    name: str
    enabled: bool = True
    schedule: CronSchedule = field(default_factory=lambda: CronSchedule(kind="every"))
    payload: CronPayload = field(default_factory=CronPayload)
    state: CronJobState = field(default_factory=CronJobState)
    created_at_ms: int = 0
    updated_at_ms: int = 0
    delete_after_run: bool = False


@dataclass
class CronStore:
    """Cron 作业的持久化存储。"""
    version: int = 1
    jobs: list[CronJob] = field(default_factory=list)
