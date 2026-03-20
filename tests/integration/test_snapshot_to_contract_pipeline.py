"""Story 1 + 2 集成：HTML → JobPostingSnapshot → 契约校验（RequirementAnalysis / Proposal）."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nomadnomad.ingest import parse_upwork_job_html
from nomadnomad.preview import (
    example_proposal_payload_from_snapshot,
    requirement_payload_from_snapshot,
)
from nomadnomad.schemas import parse_proposal, parse_requirement_analysis

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_HTML_PATH = REPO_ROOT / "resources" / "demo" / "demo_requirement.html"


@pytest.fixture
def demo_job_html() -> str:
    return DEMO_HTML_PATH.read_text(encoding="utf-8")


def test_demo_html_flows_into_requirement_analysis_and_proposal(demo_job_html: str) -> None:
    """Golden HTML → 快照 → Story 2 Schema：字段对齐且 JSON 字符串可再解析。"""
    snapshot = parse_upwork_job_html(demo_job_html)

    requirement_payload = requirement_payload_from_snapshot(snapshot)
    analysis = parse_requirement_analysis(requirement_payload)

    assert analysis.source_job_uid == snapshot.job_uid == "2034153922546495276"
    assert set(analysis.technology_stack) == set(snapshot.mandatory_skills) == {"Automation", "Python"}
    assert "Python-based" in " ".join(analysis.key_requirements)
    assert "latency" in " ".join(analysis.key_requirements).lower()
    assert analysis.budget_summary is not None
    assert "10" in analysis.budget_summary and "40" in analysis.budget_summary
    assert analysis.timeline_summary is not None
    assert "1 to 3 months" in analysis.timeline_summary
    assert analysis.complexity_notes == "Intermediate"
    assert analysis.risk_notes is not None
    assert "50+" in analysis.risk_notes

    analysis_from_json = parse_requirement_analysis(json.dumps(requirement_payload, ensure_ascii=False))
    assert analysis_from_json.model_dump() == analysis.model_dump()

    proposal_payload = example_proposal_payload_from_snapshot(snapshot)
    proposal = parse_proposal(proposal_payload)
    assert snapshot.job_uid in proposal.title
    assert snapshot.title in proposal.body_markdown
    assert proposal.template_variables.get("source_job_uid") == snapshot.job_uid
