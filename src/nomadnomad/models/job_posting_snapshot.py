"""职位帖子快照及相关值对象。

本模块仅包含数据结构定义，不包含 HTML 解析或任何 I/O 逻辑。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class JobBudget(BaseModel):
    """预算区间（以页面展示为准，单位 USD）。"""

    min_usd: float | None = None
    max_usd: float | None = None
    basis: str | None = None  # e.g. hourly


class JobEngagement(BaseModel):
    """用工形态（保留原文片段，便于 DOM 变更时仍可读）。"""

    hours_per_week_text: str | None = None
    duration_text: str | None = None
    experience_level_text: str | None = None
    project_type_text: str | None = None


class JobActivity(BaseModel):
    """职位活跃度（申请人数、面试中等）。"""

    proposals_text: str | None = None
    last_viewed_by_client_text: str | None = None
    interviewing_count: int | None = None
    invites_sent: int | None = None
    unanswered_invites: int | None = None


class ClientProfile(BaseModel):
    """About the client 区块摘要。"""

    payment_verified: bool | None = None
    rating_value: float | None = None
    reviews_text: str | None = None
    country: str | None = None
    city: str | None = None
    jobs_posted_text: str | None = None
    hire_stats_text: str | None = None
    total_spent_text: str | None = None
    avg_hourly_rate_paid_text: str | None = None
    industry: str | None = None
    company_size_text: str | None = None
    member_since_text: str | None = None


class JobPostingSnapshot(BaseModel):
    """从 Upwork 职位详情 HTML 解析得到的职位快照。"""

    source_type: str = "upwork_job_card"
    parser_version: str = "1"
    job_uid: str | None = None
    title: str | None = None
    posted_text: str | None = None
    client_location_text: str | None = None
    summary_text: str | None = None
    budget: JobBudget | None = None
    engagement: JobEngagement | None = None
    connects_required: int | None = None
    connects_available: int | None = None
    screening_questions: list[str] = Field(default_factory=list)
    mandatory_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    activity: JobActivity | None = None
    client: ClientProfile | None = None
