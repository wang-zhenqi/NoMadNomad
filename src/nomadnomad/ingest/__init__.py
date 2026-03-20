"""摄取与解析：外部来源 → 领域快照。

公开入口与模型可从本包导入；领域模型定义在 `nomadnomad.models`。
"""

from nomadnomad.ingest.errors import HtmlParseError
from nomadnomad.ingest.upwork_job_html_parser import parse_upwork_job_html
from nomadnomad.models import (
    ClientProfile,
    JobActivity,
    JobBudget,
    JobEngagement,
    JobPostingSnapshot,
)

__all__ = [
    "ClientProfile",
    "HtmlParseError",
    "JobActivity",
    "JobBudget",
    "JobEngagement",
    "JobPostingSnapshot",
    "parse_upwork_job_html",
]
