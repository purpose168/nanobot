---
name: weather
description: 获取当前天气和预报（无需 API 密钥）。
homepage: https://wttr.in/:help
metadata: {"nanobot":{"emoji":"🌤️","requires":{"bins":["curl"]}}}
---

# 天气（Weather）

两个免费服务，无需 API 密钥。

## wttr.in（主要服务）

快速单行命令：
```bash
curl -s "wttr.in/London?format=3"  # 使用静默模式获取伦敦的天气，格式 3 表示简洁格式
# 输出：London: ⛅️ +8°C
```

紧凑格式：
```bash
curl -s "wttr.in/London?format=%l:+%c+%t+%h+%w"  # 使用自定义格式获取伦敦的天气，%l 表示位置，%c 表示天气状况，%t 表示温度，%h 表示湿度，%w 表示风速
# 输出：London: ⛅️ +8°C 71% ↙5km/h
```

完整预报：
```bash
curl -s "wttr.in/London?T"  # 使用静默模式获取伦敦的完整天气预报，T 参数启用终端视图
```

格式代码：`%c` 天气状况 · `%t` 温度 · `%h` 湿度 · `%w` 风速 · `%l` 位置 · `%m` 月相

提示：
- URL 编码空格：`wttr.in/New+York`（将空格替换为 + 号）
- 机场代码：`wttr.in/JFK`（使用机场代码代替城市名）
- 单位：`?m`（公制）`?u`（美制单位）
- 仅今天：`?1` · 仅当前：`?0`
- PNG：`curl -s "wttr.in/Berlin.png" -o /tmp/weather.png`（下载天气图片到指定路径）

## Open-Meteo（回退服务，JSON）

免费，无需密钥，适合程序化使用：
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current_weather=true"  # 使用静默模式查询指定纬度和经度的当前天气，返回 JSON 格式数据
```

先查找城市的坐标，然后查询。返回包含温度、风速、天气代码的 JSON 数据。

文档：https://open-meteo.com/en/docs
