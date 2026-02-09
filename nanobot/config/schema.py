"""使用 Pydantic 的配置模式。"""

from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class WhatsAppConfig(BaseModel):
    """WhatsApp 通道配置。"""
    enabled: bool = False
    bridge_url: str = "ws://localhost:3001"
    allow_from: list[str] = Field(default_factory=list)  # 允许的电话号码


class TelegramConfig(BaseModel):
    """Telegram 通道配置。"""
    enabled: bool = False
    token: str = ""  # 来自 @BotFather 的机器人令牌
    allow_from: list[str] = Field(default_factory=list)  # 允许的用户 ID 或用户名
    proxy: str | None = None  # HTTP/SOCKS5 代理 URL，例如 "http://127.0.0.1:7890" 或 "socks5://127.0.0.1:1080"


class FeishuConfig(BaseModel):
    """使用 WebSocket 长连接的 Feishu/Lark 通道配置。"""
    enabled: bool = False
    app_id: str = ""  # 来自 Feishu 开放平台的 App ID
    app_secret: str = ""  # 来自 Feishu 开放平台的 App Secret
    encrypt_key: str = ""  # 用于事件订阅的加密密钥（可选）
    verification_token: str = ""  # 用于事件订阅的验证令牌（可选）
    allow_from: list[str] = Field(default_factory=list)  # 允许的用户 open_ids


class DiscordConfig(BaseModel):
    """Discord 通道配置。"""
    enabled: bool = False
    token: str = ""  # 来自 Discord 开发者门户的机器人令牌
    allow_from: list[str] = Field(default_factory=list)  # 允许的用户 ID
    gateway_url: str = "wss://gateway.discord.gg/?v=10&encoding=json"
    intents: int = 37377  # GUILDS + GUILD_MESSAGES + DIRECT_MESSAGES + MESSAGE_CONTENT（Discord 意图标志）


class ChannelsConfig(BaseModel):
    """聊天通道的配置。"""
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    feishu: FeishuConfig = Field(default_factory=FeishuConfig)


class AgentDefaults(BaseModel):
    """默认智能体配置。"""
    workspace: str = "~/.nanobot/workspace"
    model: str = "anthropic/claude-opus-4-5"
    max_tokens: int = 8192
    temperature: float = 0.7
    max_tool_iterations: int = 20


class AgentsConfig(BaseModel):
    """智能体配置。"""
    defaults: AgentDefaults = Field(default_factory=AgentDefaults)


class ProviderConfig(BaseModel):
    """LLM 提供商配置。"""
    api_key: str = ""
    api_base: str | None = None
    extra_headers: dict[str, str] | None = None  # 自定义标头（例如 AiHubMix 的 APP-Code）


class ProvidersConfig(BaseModel):
    """LLM 提供商的配置。"""
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = Field(default_factory=ProviderConfig)
    dashscope: ProviderConfig = Field(default_factory=ProviderConfig)  # 阿里云通义千问
    vllm: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    moonshot: ProviderConfig = Field(default_factory=ProviderConfig)
    aihubmix: ProviderConfig = Field(default_factory=ProviderConfig)  # AiHubMix API 网关


class GatewayConfig(BaseModel):
    """网关/服务器配置。"""
    host: str = "0.0.0.0"
    port: int = 18790


class WebSearchConfig(BaseModel):
    """Web 搜索工具配置。"""
    api_key: str = ""  # Brave Search API 密钥
    max_results: int = 5


class WebToolsConfig(BaseModel):
    """Web 工具配置。"""
    search: WebSearchConfig = Field(default_factory=WebSearchConfig)


class ExecToolConfig(BaseModel):
    """Shell 执行工具配置。"""
    timeout: int = 60


class ToolsConfig(BaseModel):
    """工具配置。"""
    web: WebToolsConfig = Field(default_factory=WebToolsConfig)
    exec: ExecToolConfig = Field(default_factory=ExecToolConfig)
    restrict_to_workspace: bool = False  # 如果为 true，则将所有工具访问限制在工作空间目录中


class Config(BaseSettings):
    """nanobot 的根配置。"""
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    
    @property
    def workspace_path(self) -> Path:
        """获取展开的工作空间路径。"""
        return Path(self.agents.defaults.workspace).expanduser()
    
    def get_provider(self, model: str | None = None) -> ProviderConfig | None:
        """获取匹配的提供商配置（api_key、api_base、extra_headers）。回退到第一个可用的。"""
        from nanobot.providers.registry import PROVIDERS
        model_lower = (model or self.agents.defaults.model).lower()

        # Match by keyword (order follows PROVIDERS registry)
        # 按关键字匹配（顺序遵循 PROVIDERS 注册表）
        for spec in PROVIDERS:
            p = getattr(self.providers, spec.name, None)
            if p and any(kw in model_lower for kw in spec.keywords) and p.api_key:
                return p

        # Fallback: gateways first, then others (follows registry order)
        # 回退：首先网关，然后其他（遵循注册表顺序）
        for spec in PROVIDERS:
            p = getattr(self.providers, spec.name, None)
            if p and p.api_key:
                return p
        return None

    def get_api_key(self, model: str | None = None) -> str | None:
        """获取给定模型的 API 密钥。回退到第一个可用的密钥。"""
        p = self.get_provider(model)
        return p.api_key if p else None
    
    def get_api_base(self, model: str | None = None) -> str | None:
        """获取给定模型的 API 基础 URL。为已知的网关应用默认 URL。"""
        from nanobot.providers.registry import PROVIDERS
        p = self.get_provider(model)
        if p and p.api_base:
            return p.api_base
        # Only gateways get a default URL here. Standard providers (like Moonshot)
        # 只有网关在这里获得默认 URL。标准提供商（如 Moonshot）
        # handle their base URL via env vars in _setup_env, NOT via api_base —
        # 通过 _setup_env 中的环境变量处理其基础 URL，而不是通过 api_base —
        # otherwise find_gateway() would misdetect them as local/vLLM.
        # 否则 find_gateway() 会将它们误检测为本地/vLLM。
        for spec in PROVIDERS:
            if spec.is_gateway and spec.default_api_base and p == getattr(self.providers, spec.name, None):
                return spec.default_api_base
        return None
    
    class Config:
        env_prefix = "NANOBOT_"
        env_nested_delimiter = "__"
