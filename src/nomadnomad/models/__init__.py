"""领域数据模型（Pydantic），与摄取/解析等业务逻辑分离。"""

from nomadnomad.models.job_posting_snapshot import (
    ClientProfile,
    JobActivity,
    JobBudget,
    JobEngagement,
    JobPostingSnapshot,
)
from nomadnomad.models.proposal import Proposal
from nomadnomad.models.requirement_analysis import RequirementAnalysis

__all__ = [
    "ClientProfile",
    "JobActivity",
    "JobBudget",
    "JobEngagement",
    "JobPostingSnapshot",
    "Proposal",
    "RequirementAnalysis",
]
