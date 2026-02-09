---
name: summarize
description: 从 URL、播客和本地文件中摘要或提取文本/转录（"转录此 YouTube/视频"的绝佳回退方案）。
homepage: https://summarize.sh
metadata: {"nanobot":{"emoji":"🧾","requires":{"bins":["summarize"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/summarize","bins":["summarize"],"label":"Install summarize (brew)"}]}}
---

# 摘要工具（Summarize）

用于摘要 URL、本地文件和 YouTube 链接的快速命令行工具。

## 何时使用（触发短语）

当用户询问以下任何内容时立即使用此技能：
- "使用 summarize.sh"
- "这个链接/视频是关于什么的？"
- "摘要此 URL/文章"
- "转录此 YouTube/视频"（尽力提取转录；无需 `yt-dlp`）

## 快速开始

```bash
summarize "https://example.com" --model google/gemini-3-flash-preview  # 摘要指定的 URL，使用 Google Gemini 3 Flash Preview 模型
summarize "/path/to/file.pdf" --model google/gemini-3-flash-preview  # 摘要指定的本地 PDF 文件，使用 Google Gemini 3 Flash Preview 模型
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto  # 摘要指定的 YouTube 视频，自动处理转录
```

## YouTube：摘要 vs 转录

尽力转录（仅限 URL）：

```bash
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto --extract-only  # 仅提取 YouTube 视频的转录文本，不进行摘要
```

如果用户要求转录但内容很大，首先返回一个紧凑的摘要，然后询问要扩展哪个部分/时间范围。

## 模型 + 密钥

为您选择的提供商设置 API 密钥：
- OpenAI：`OPENAI_API_KEY`
- Anthropic：`ANTHROPIC_API_KEY`
- xAI：`XAI_API_KEY`
- Google：`GEMINI_API_KEY`（别名：`GOOGLE_GENERATIVE_AI_API_KEY`、`GOOGLE_API_KEY`）

如果未设置，默认模型为 `google/gemini-3-flash-preview`。

## 有用的标志

- `--length short|medium|long|xl|xxl|<chars>` - 设置摘要长度
- `--max-output-tokens <count>` - 设置最大输出 token 数
- `--extract-only`（仅限 URL）- 仅提取文本，不摘要
- `--json`（机器可读）- 以 JSON 格式输出
- `--firecrawl auto|off|always`（回退提取）- Firecrawl 提取模式
- `--youtube auto`（如果设置了 `APIFY_API_TOKEN`，则使用 Apify 回退）- YouTube 处理模式

## 配置

可选配置文件：`~/.summarize/config.json`

```json
{ "model": "openai/gpt-5.2" }  # 设置默认模型为 OpenAI GPT-5.2
```

可选服务：
- `FIRECRAWL_API_KEY` 用于被阻止的网站
- `APIFY_API_TOKEN` 用于 YouTube 回退
