"""Upwork 职位页 DOM 抽取：按页面区块拆分子模块，再由解析入口编排。

子模块：
- `text`：空白规范化
- `listing`：标题、摘要、Connects、listing 级地区
- `engagement`：工时/周期/经验、预算、项目类型
- `screening_skills`：投标问题、必备技能
- `activity`：职位活跃度
- `client_profile`：About the client
"""

from __future__ import annotations

from nomadnomad.ingest.upwork.activity import extract_activity
from nomadnomad.ingest.upwork.client_profile import extract_client_profile
from nomadnomad.ingest.upwork.engagement import extract_budget, extract_engagement, extract_project_type
from nomadnomad.ingest.upwork.listing import (
    extract_client_location_listing,
    extract_connects_available,
    extract_connects_required,
    extract_job_uid,
    extract_posted_text,
    extract_summary,
    extract_title,
)
from nomadnomad.ingest.upwork.screening_skills import extract_mandatory_skills, extract_screening_questions
from nomadnomad.ingest.upwork.text import normalize_ws

__all__ = [
    "extract_activity",
    "extract_budget",
    "extract_client_location_listing",
    "extract_client_profile",
    "extract_connects_available",
    "extract_connects_required",
    "extract_engagement",
    "extract_job_uid",
    "extract_mandatory_skills",
    "extract_posted_text",
    "extract_project_type",
    "extract_screening_questions",
    "extract_summary",
    "extract_title",
    "normalize_ws",
]
