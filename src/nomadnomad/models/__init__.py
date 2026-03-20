"""领域数据模型（Pydantic），与摄取/解析等业务逻辑分离。"""

from nomadnomad.models.job_posting_snapshot import (
    ClientProfile,
    JobActivity,
    JobBudget,
    JobEngagement,
    JobPostingSnapshot,
)

__all__ = [
    "ClientProfile",
    "JobActivity",
    "JobBudget",
    "JobEngagement",
    "JobPostingSnapshot",
]
