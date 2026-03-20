"""Upwork 提案草稿的结构化契约（正文为 Markdown）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Proposal(BaseModel):
    """提案标题、Markdown 正文及可选模板变量（如称呼、项目名占位）。"""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)
    template_variables: dict[str, str] = Field(default_factory=dict)
