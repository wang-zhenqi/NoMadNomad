"""Story 1：HTML → JobPostingSnapshot（GWT 映射）."""

from __future__ import annotations

from pathlib import Path

import pytest

from nomadnomad.ingest import HtmlParseError, parse_upwork_job_html

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_HTML_PATH = REPO_ROOT / "resources" / "demo" / "demo_requirement.html"


def _demo_html() -> str:
    return DEMO_HTML_PATH.read_text(encoding="utf-8")


def _norm(s: str) -> str:
    return " ".join(s.split())


@pytest.fixture
def demo_html() -> str:
    return _demo_html()


def test_s1_10_empty_input_raises() -> None:
    """S1-10: 空字符串 → 明确错误。"""
    with pytest.raises(HtmlParseError, match="empty input"):
        parse_upwork_job_html("")
    with pytest.raises(HtmlParseError, match="empty input"):
        parse_upwork_job_html("   \n\t  ")


def test_s1_11_plain_text_raises_not_attribute_error() -> None:
    """S1-11: 无结构纯文本 → 封装为 HtmlParseError，不抛 AttributeError。"""
    with pytest.raises(HtmlParseError) as exc_info:
        parse_upwork_job_html("not a job posting at all")
    assert not isinstance(exc_info.value, AttributeError)


def test_s1_12_missing_title_raises() -> None:
    """S1-12: 无职位标题 → missing job title。"""
    html = "<html><body><p>Some content without job header</p></body></html>"
    with pytest.raises(HtmlParseError, match="missing job title"):
        parse_upwork_job_html(html)


def test_s1_13_parse_is_deterministic(demo_html: str) -> None:
    """S1-13: 同一 HTML 两次解析结果一致。"""
    a = parse_upwork_job_html(demo_html).model_dump()
    b = parse_upwork_job_html(demo_html).model_dump()
    assert a == b


def test_s1_01_title(demo_html: str) -> None:
    """S1-01: 标题正确。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.title == "Automated Image Solving (LLM or Human-in-the-loop)"


def test_s1_02_job_uid(demo_html: str) -> None:
    """S1-02: job_uid 与 DOM 一致。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.job_uid == "2034153922546495276"


def test_s1_03_summary_keywords(demo_html: str) -> None:
    """S1-03: Summary 关键句存在。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.summary_text is not None
    assert "Python-based system" in snap.summary_text
    assert "within 5s" in snap.summary_text


def test_s1_04_mandatory_skills(demo_html: str) -> None:
    """S1-04: 必备技能。"""
    snap = parse_upwork_job_html(demo_html)
    assert set(snap.mandatory_skills) == {"Automation", "Python"}


def test_s1_05_screening_questions(demo_html: str) -> None:
    """S1-05: 两条投标问题与原文一致（空白归一化）。"""
    snap = parse_upwork_job_html(demo_html)
    assert len(snap.screening_questions) == 2
    expected_1 = _norm(
        "Have you worked on other similar image solving projects? "
        "Any of them that required custom solving, or the use of LLM? Please describe."
    )
    expected_2 = _norm(
        "Do you have any experience working with human-in-the-loop systems that can help "
        "answer our images if LLMs cannot? If so, describe that experience."
    )
    assert _norm(snap.screening_questions[0]) == expected_1
    assert _norm(snap.screening_questions[1]) == expected_2


def test_s1_06_budget_hourly(demo_html: str) -> None:
    """S1-06: 预算区间与 hourly。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.budget is not None
    assert snap.budget.min_usd == 10.0
    assert snap.budget.max_usd == 40.0
    assert snap.budget.basis == "hourly"


def test_s1_07_engagement(demo_html: str) -> None:
    """S1-07: 用工形态原文/字段。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.engagement is not None
    assert snap.engagement.hours_per_week_text == "Less than 30 hrs/week"
    assert snap.engagement.duration_text == "1 to 3 months"
    assert snap.engagement.experience_level_text == "Intermediate"
    assert snap.engagement.project_type_text == "Ongoing project"


def test_s1_08_client_payment_rating_country(demo_html: str) -> None:
    """S1-08: 客户付款、评分、国家。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.client is not None
    assert snap.client.payment_verified is True
    assert snap.client.rating_value == 5.0
    assert snap.client.country is not None
    assert "United States" in snap.client.country


def test_s1_09_activity_proposals_interviewing(demo_html: str) -> None:
    """S1-09: 申请量与面试中人数。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.activity is not None
    assert snap.activity.proposals_text == "50+"
    assert snap.activity.interviewing_count == 8


def test_connects_parsed(demo_html: str) -> None:
    """Connects 区块（验收标准隐含）。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.connects_required == 15
    assert snap.connects_available == 135


def test_posted_and_worldwide(demo_html: str) -> None:
    """发布时间与客户可见地区（listing 顶部）。"""
    snap = parse_upwork_job_html(demo_html)
    assert snap.posted_text is not None
    assert "Posted" in snap.posted_text
    assert "2 days ago" in snap.posted_text
    assert snap.client_location_text == "Worldwide"
