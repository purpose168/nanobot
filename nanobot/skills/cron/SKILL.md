---
name: cron
description: 安排提醒和重复任务。
---

# Cron（定时任务）

使用 `cron` 工具来安排提醒或重复任务。

## 两种模式

1. **提醒（Reminder）** - 消息直接发送给用户
2. **任务（Task）** - 消息是任务描述，代理执行并发送结果

## 示例

固定提醒：
```
cron(action="add", message="Time to take a break!", every_seconds=1200)  # 添加一个每20分钟（1200秒）发送一次的提醒消息
```

动态任务（代理每次都执行）：
```
cron(action="add", message="Check HKUDS/nanobot GitHub stars and report", every_seconds=600)  # 添加一个每10分钟（600秒）检查一次GitHub星标数量的任务，代理将执行并报告结果
```

列表/移除：
```
cron(action="list")  # 列出所有当前安排的定时任务
cron(action="remove", job_id="abc123")  # 移除指定ID的定时任务
```

## 时间表达式

| 用户表述 | 参数 |
|-----------|------------|
| 每20分钟 | every_seconds: 1200 |
| 每小时 | every_seconds: 3600 |
| 每天上午8点 | cron_expr: "0 8 * * *" |
| 工作日下午5点 | cron_expr: "0 17 * * 1-5" |
