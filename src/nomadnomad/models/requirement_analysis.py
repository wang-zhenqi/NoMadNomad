"""需求分析结构化输出（Agent / API 共用的领域契约）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RequirementAnalysis(BaseModel):
    """从职位快照或描述归纳出的需求分析结果。

    与 `JobPostingSnapshot` 的关联通过可选字段 `source_job_uid` 表达；其余字段为分析结论。
    未知或不适用的维度可留空字符串或 ``None``（由调用方约定）；LLM 输出的多余键名会被忽略。
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    technology_stack: list[str] = Field(default_factory=list)
    key_requirements: list[str] = Field(default_factory=list)
    budget_summary: str | None = None
    timeline_summary: str | None = None
    complexity_notes: str | None = None
    risk_notes: str | None = None
    source_job_uid: str | None = None
