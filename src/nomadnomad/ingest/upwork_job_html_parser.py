"""Upwork 职位 HTML → `JobPostingSnapshot` 的解析入口（编排抽取与校验）。"""

from __future__ import annotations

from bs4 import BeautifulSoup

from nomadnomad.ingest import upwork as ex
from nomadnomad.ingest.errors import HtmlParseError
from nomadnomad.models.job_posting_snapshot import JobPostingSnapshot


def parse_upwork_job_html(html: str) -> JobPostingSnapshot:
    """解析 Upwork 职位卡片 HTML，返回通过校验的快照。

    Raises:
        HtmlParseError: 空输入、缺少职位标题等不可恢复问题。
    """
    if not html or not html.strip():
        raise HtmlParseError("empty input")

    soup = BeautifulSoup(html, "html.parser")
    title = ex.extract_title(soup)
    if not title:
        raise HtmlParseError("missing job title")

    return JobPostingSnapshot(
        job_uid=ex.extract_job_uid(soup),
        title=title,
        posted_text=ex.extract_posted_text(soup),
        client_location_text=ex.extract_client_location_listing(soup),
        summary_text=ex.extract_summary(soup),
        budget=ex.extract_budget(soup),
        engagement=ex.extract_engagement(soup),
        connects_required=ex.extract_connects_required(html),
        connects_available=ex.extract_connects_available(html),
        screening_questions=ex.extract_screening_questions(soup),
        mandatory_skills=ex.extract_mandatory_skills(soup),
        activity=ex.extract_activity(soup),
        client=ex.extract_client_profile(soup),
    )
