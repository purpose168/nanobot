<div align="center">
  <img src="nanobot_logo.png" alt="nanobot" width="500">
  <h1>nanobot: 超轻量级个人 AI 助手</h1>
  <p>
    <a href="https://pypi.org/project/nanobot-ai/"><img src="https://img.shields.io/pypi/v/nanobot-ai" alt="PyPI"></a>
    <a href="https://pepy.tech/project/nanobot-ai"><img src="https://static.pepy.tech/badge/nanobot-ai" alt="Downloads"></a>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/Feishu-Group-E9DBFC?style=flat&logo=feishu&logoColor=white" alt="Feishu"></a>
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/WeChat-Group-C5EAB4?style=flat&logo=wechat&logoColor=white" alt="WeChat"></a>
    <a href="https://discord.gg/MnCvHqpUGB"><img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord"></a>
  </p>
</div>

🐈 **nanobot** 是一个**超轻量级**个人 AI 助手，灵感来源于 [Clawdbot](https://github.com/openclaw/openclaw)

⚡️ 仅用**约 4,000** 行代码实现核心智能体功能 —— 比 Clawdbot 的 43 万+ 行代码**小 99%**。

📏 实时代码行数：**3,423 行**（随时运行 `bash core_agent_lines.sh` 验证）

## 📢 最新动态

- **2026-02-08** 🔧 重构了 Providers —— 添加新的 LLM 提供商现在只需 2 个简单步骤！查看 [这里](#providers)。
- **2026-02-07** 🚀 发布了 v0.1.3.post5 版本，支持 Qwen 模型并进行了多项关键改进！查看 [这里](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post5) 了解详情。
- **2026-02-06** ✨ 添加了 Moonshot/Kimi 提供商、Discord 集成和增强的安全加固！
- **2026-02-05** ✨ 添加了飞书通道、DeepSeek 提供商和增强的定时任务支持！
- **2026-02-04** 🚀 发布了 v0.1.3.post4 版本，支持多提供商和 Docker！查看 [这里](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post4) 了解详情。
- **2026-02-03** ⚡ 集成了 vLLM 以支持本地 LLM 和改进的自然语言任务调度！
- **2026-02-02** 🎉 nanobot 正式发布！欢迎尝试 🐈 nanobot！

## nanobot 的核心特性：

🪶 **超轻量级**：核心智能体代码仅约 4,000 行 —— 比 Clawdbot 小 99%。

🔬 **研究就绪**：代码整洁易读，易于理解、修改和扩展，适合研究使用。

⚡️ **闪电般快速**：最小化的代码足迹意味着更快的启动速度、更低的资源占用和更快的迭代。

💎 **易于使用**：一键部署，即可开始使用。

## 🏗️ 架构

<p align="center">
  <img src="nanobot_arch.png" alt="nanobot architecture" width="800">
</p>

## ✨ 功能

<table align="center">
  <tr align="center">
    <th><p align="center">📈 24/7 实时市场分析</p></th>
    <th><p align="center">🚀 全栈软件工程师</p></th>
    <th><p align="center">📅 智能日常管理助手</p></th>
    <th><p align="center">📚 个人知识助手</p></th>
  </tr>
  <tr>
    <td align="center"><p align="center"><img src="case/search.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/code.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/scedule.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/memory.gif" width="180" height="400"></p></td>
  </tr>
  <tr>
    <td align="center">发现 • 洞察 • 趋势</td>
    <td align="center">开发 • 部署 • 扩展</td>
    <td align="center">计划 • 自动化 • 组织</td>
    <td align="center">学习 • 记忆 • 推理</td>
  </tr>
</table>

## 📦 安装

**从源码安装**（最新特性，推荐用于开发）

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e .
```

**使用 [uv](https://github.com/astral-sh/uv) 安装**（稳定，快速）

```bash
uv tool install nanobot-ai
```

**从 PyPI 安装**（稳定）

```bash
pip install nanobot-ai
```

## 🚀 快速开始

> [!TIP]
> 在 `~/.nanobot/config.json` 中设置您的 API 密钥。
> 获取 API 密钥：[OpenRouter](https://openrouter.ai/keys)（全球）· [DashScope](https://dashscope.console.aliyun.com)（Qwen）· [Brave Search](https://brave.com/search/api/)（可选，用于网络搜索）

**1. 初始化**

```bash
nanobot onboard
```

**2. 配置** (`~/.nanobot/config.json`)

对于 OpenRouter - 推荐全球用户使用：
```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    }
  }
}
```

**3. 聊天**

```bash
nanobot agent -m "What is 2+2?"
```

就是这样！您在 2 分钟内拥有了一个可用的 AI 助手。

## 🖥️ 本地模型 (vLLM)

使用 vLLM 或任何兼容 OpenAI 的服务器运行您自己的本地模型。

**1. 启动 vLLM 服务器**

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

**2. 配置** (`~/.nanobot/config.json`)

```json
{
  "providers": {
    "vllm": {
      "apiKey": "dummy",
      "apiBase": "http://localhost:8000/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "meta-llama/Llama-3.1-8B-Instruct"
    }
  }
}
```

**3. 聊天**

```bash
nanobot agent -m "Hello from my local LLM!"
```

> [!TIP]
> 对于不需要身份验证的本地服务器，`apiKey` 可以是任何非空字符串。

## 💬 聊天应用

通过 Telegram、Discord、WhatsApp 或飞书与您的 nanobot 交流 —— 随时随地。

| 通道 | 设置难度 |
|---------|-------|
| **Telegram** | 简单（只需一个令牌） |
| **Discord** | 简单（机器人令牌 + 意图） |
| **WhatsApp** | 中等（扫描二维码） |
| **Feishu** | 中等（应用凭证） |

<details>
<summary><b>Telegram</b>（推荐）</summary>

**1. 创建机器人**
- 打开 Telegram，搜索 `@BotFather`
- 发送 `/newbot`，按照提示操作
- 复制令牌

**2. 配置**

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

> 从 Telegram 上的 `@userinfobot` 获取您的用户 ID。

**3. 运行**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Discord</b></summary>

**1. 创建机器人**
- 前往 https://discord.com/developers/applications
- 创建应用 → Bot → Add Bot
- 复制机器人令牌

**2. 启用意图**
- 在 Bot 设置中，启用 **MESSAGE CONTENT INTENT**
- （可选）如果您计划使用基于成员数据的允许列表，请启用 **SERVER MEMBERS INTENT**

**3. 获取您的用户 ID**
- Discord 设置 → 高级 → 启用 **开发者模式**
- 右键点击您的头像 → **复制用户 ID**

**4. 配置**

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

**5. 邀请机器人**
- OAuth2 → URL Generator
- Scopes: `bot`
- Bot Permissions: `Send Messages`, `Read Message History`
- 打开生成的邀请 URL 并将机器人添加到您的服务器

**6. 运行**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>WhatsApp</b></summary>

需要 **Node.js ≥18**。

**1. 链接设备**

```bash
nanobot channels login
# 使用 WhatsApp 扫描二维码 → 设置 → 链接设备
```

**2. 配置**

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "allowFrom": ["+1234567890"]
    }
  }
}
```

**3. 运行**（两个终端）

```bash
# 终端 1
nanobot channels login

# 终端 2
nanobot gateway
```

</details>

<details>
<summary><b>Feishu (飞书)</b></summary>

使用 **WebSocket** 长连接 —— 无需公网 IP。

```bash
pip install nanobot-ai[feishu]
```

**1. 创建飞书机器人**
- 访问 [飞书开放平台](https://open.feishu.cn/app)
- 创建新应用 → 启用 **Bot** 能力
- **权限**：添加 `im:message`（发送消息）
- **事件**：添加 `im.message.receive_v1`（接收消息）
  - 选择 **长连接** 模式（需要先运行 nanobot 以建立连接）
- 从 "凭证与基础信息" 获取 **App ID** 和 **App Secret**
- 发布应用

**2. 配置**

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "xxx",
      "encryptKey": "",
      "verificationToken": "",
      "allowFrom": []
    }
  }
}
```

> `encryptKey` 和 `verificationToken` 对于长连接模式是可选的。
> `allowFrom`：留空以允许所有用户，或添加 `["ou_xxx"]` 以限制访问。

**3. 运行**

```bash
nanobot gateway
```

> [!TIP]
> 飞书使用 WebSocket 接收消息 —— 无需 webhook 或公网 IP！

</details>

## ⚙️ 配置

配置文件：`~/.nanobot/config.json`

### Providers

> [!NOTE]
> Groq 通过 Whisper 提供免费的语音转录。如果配置了，Telegram 语音消息将被自动转录。

| Provider | 用途 | 获取 API 密钥 |
|----------|---------|-------------|
| `openrouter` | LLM（推荐，访问所有模型） | [openrouter.ai](https://openrouter.ai) |
| `anthropic` | LLM（直接访问 Claude） | [console.anthropic.com](https://console.anthropic.com) |
| `openai` | LLM（直接访问 GPT） | [platform.openai.com](https://platform.openai.com) |
| `deepseek` | LLM（直接访问 DeepSeek） | [platform.deepseek.com](https://platform.deepseek.com) |
| `groq` | LLM + **语音转录**（Whisper） | [console.groq.com](https://console.groq.com) |
| `gemini` | LLM（直接访问 Gemini） | [aistudio.google.com](https://aistudio.google.com) |
| `aihubmix` | LLM（API 网关，访问所有模型） | [aihubmix.com](https://aihubmix.com) |
| `dashscope` | LLM（Qwen） | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |
| `moonshot` | LLM（Moonshot/Kimi） | [platform.moonshot.cn](https://platform.moonshot.cn) |
| `zhipu` | LLM（智谱 GLM） | [open.bigmodel.cn](https://open.bigmodel.cn) |
| `vllm` | LLM（本地，任何兼容 OpenAI 的服务器） | — |

<details>
<summary><b>添加新 Provider（开发者指南）</b></summary>

nanobot 使用 **Provider Registry** (`nanobot/providers/registry.py`) 作为单一数据源。
添加新 provider 只需 **2 个步骤** —— 无需修改 if-elif 链。

**步骤 1.** 在 `nanobot/providers/registry.py` 中的 `PROVIDERS` 添加 `ProviderSpec` 条目：

```python
ProviderSpec(
    name="myprovider",                   # 配置字段名
    keywords=("myprovider", "mymodel"),  # 用于自动匹配的模型名称关键字
    env_key="MYPROVIDER_API_KEY",        # LiteLLM 的环境变量
    display_name="My Provider",          # 在 `nanobot status` 中显示
    litellm_prefix="myprovider",         # 自动前缀: model → myprovider/model
    skip_prefixes=("myprovider/",),      # 不要双重前缀
)
```

**步骤 2.** 在 `nanobot/config/schema.py` 中的 `ProvidersConfig` 添加字段：

```python
class ProvidersConfig(BaseModel):
    ...
    myprovider: ProviderConfig = ProviderConfig()
```

就是这样！环境变量、模型前缀、配置匹配和 `nanobot status` 显示都将自动工作。

**常见 `ProviderSpec` 选项：**

| 字段 | 描述 | 示例 |
|-------|-------------|---------|
| `litellm_prefix` | 为 LiteLLM 自动添加模型名称前缀 | `"dashscope"` → `dashscope/qwen-max` |
| `skip_prefixes` | 如果模型已经以这些开头，则不要添加前缀 | `("dashscope/", "openrouter/")` |
| `env_extras` | 要设置的额外环境变量 | `(("ZHIPUAI_API_KEY", "{api_key}"),)` |
| `model_overrides` | 按模型参数覆盖 | `(("kimi-k2.5", {"temperature": 1.0}),)` |
| `is_gateway` | 可以路由任何模型（如 OpenRouter） | `True` |
| `detect_by_key_prefix` | 通过 API 密钥前缀检测网关 | `"sk-or-"` |
| `detect_by_base_keyword` | 通过 API 基础 URL 检测网关 | `"openrouter"` |
| `strip_model_prefix` | 在重新添加前缀之前去除现有前缀 | `True`（对于 AiHubMix） |

</details>


### 安全

> [!TIP]
> 对于生产部署，在配置中设置 `"restrictToWorkspace": true` 以沙箱化智能体。

| 选项 | 默认值 | 描述 |
|--------|---------|-------------|
| `tools.restrictToWorkspace` | `false` | 当设置为 `true` 时，将**所有**智能体工具（shell、文件读写/编辑、列表）限制在工作区目录中。防止路径遍历和超出范围的访问。 |
| `channels.*.allowFrom` | `[]`（允许所有） | 用户 ID 白名单。空 = 允许所有人；非空 = 仅列出的用户可以交互。 |


## CLI 参考

| 命令 | 描述 |
|---------|-------------|
| `nanobot onboard` | 初始化配置和工作区 |
| `nanobot agent -m "..."` | 与智能体聊天 |
| `nanobot agent` | 交互式聊天模式 |
| `nanobot gateway` | 启动网关 |
| `nanobot status` | 显示状态 |
| `nanobot channels login` | 链接 WhatsApp（扫描二维码） |
| `nanobot channels status` | 显示通道状态 |

<details>
<summary><b>定时任务（Cron）</b></summary>

```bash
# 添加任务
nanobot cron add --name "daily" --message "Good morning!" --cron "0 9 * * *"
nanobot cron add --name "hourly" --message "Check status" --every 3600

# 列出任务
nanobot cron list

# 删除任务
nanobot cron remove <job_id>
```

</details>

## 🐳 Docker

> [!TIP]
> `-v ~/.nanobot:/root/.nanobot` 标志将本地配置目录挂载到容器中，因此您的配置和工作区在容器重启后会持久化。

在容器中构建和运行 nanobot：

```bash
# 构建镜像
docker build -t nanobot .

# 初始化配置（首次使用）
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot onboard

# 在主机上编辑配置以添加 API 密钥
vim ~/.nanobot/config.json

# 运行网关（连接到 Telegram/WhatsApp）
docker run -v ~/.nanobot:/root/.nanobot -p 18790:18790 nanobot gateway

# 或运行单个命令
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot agent -m "Hello!"
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot status
```

## 📁 项目结构

```
nanobot/
├── agent/          # 🧠 核心智能体逻辑
│   ├── loop.py     #    智能体循环（LLM ↔ 工具执行）
│   ├── context.py  #    提示构建器
│   ├── memory.py   #    持久内存
│   ├── skills.py   #    技能加载器
│   ├── subagent.py #    后台任务执行
│   └── tools/      #    内置工具（包括 spawn）
├── skills/         # 🎯 捆绑技能（github, weather, tmux...）
├── channels/       # 📱 WhatsApp 集成
├── bus/            # 🚌 消息路由
├── cron/           # ⏰ 定时任务
├── heartbeat/      # 💓 主动唤醒
├── providers/      # 🤖 LLM 提供商（OpenRouter 等）
├── session/        # 💬 对话会话
├── config/         # ⚙️ 配置
└── cli/            # 🖥️ 命令
```

## 🤝 贡献与路线图

欢迎提交 PR！代码库故意保持小巧且可读。🤗

**路线图** — 选择一个项目并 [创建 PR](https://github.com/HKUDS/nanobot/pulls)！

- [x] **语音转录** — 支持 Groq Whisper（Issue #13）
- [ ] **多模态** — 看和听（图像、语音、视频）
- [ ] **长期记忆** — 永远不会忘记重要上下文
- [ ] **更好的推理** — 多步规划和反思
- [ ] **更多集成** — Discord、Slack、电子邮件、日历
- [ ] **自我改进** — 从反馈和错误中学习

### 贡献者

<a href="https://github.com/HKUDS/nanobot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=HKUDS/nanobot&max=100&columns=12" />
</a>


## ⭐ Star 历史

<div align="center">
  <a href="https://star-history.com/#HKUDS/nanobot&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date" />
      <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date" style="border-radius: 15px; box-shadow: 0 0 30px rgba(0, 217, 255, 0.3);" />
    </picture>
  </a>
</div>

<p align="center">
  <em> 感谢访问 ✨ nanobot！</em><br><br>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.nanobot&style=for-the-badge&color=00d4ff" alt="Views">
</p>


<p align="center">
  <sub>nanobot 仅用于教育、研究和技术交流目的</sub>
</p>