"""LLM 相关配置（环境变量 / .env，不写死密钥）。"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LlmSettings(BaseSettings):
    """OpenAI 兼容 Chat Completions 端点配置。"""

    model_config = SettingsConfigDict(env_prefix="NOMADNOMAD_", env_file=".env", extra="ignore")

    llm_base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI 兼容 API 根路径（含 /v1）")
    llm_model: str = Field(default="gpt-4o-mini", description="聊天补全模型名或部署名")
    llm_api_key: str | None = Field(default=None, description="API Key；未设置时仅禁止真实 HTTP 调用")
