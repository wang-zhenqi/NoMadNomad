"""Story 2：需求分析与提案契约（Schema + 校验）."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from nomadnomad.models import Proposal, RequirementAnalysis
from nomadnomad.schemas import parse_proposal, parse_requirement_analysis


def test_parse_requirement_analysis_dict_happy_path() -> None:
    """S2-01: 合法 dict → RequirementAnalysis。"""
    payload = {
        "technology_stack": ["Python", "FastAPI"],
        "key_requirements": ["REST API", "SQLite"],
        "budget_summary": "Hourly $10–$40",
        "timeline_summary": "1–3 months",
        "complexity_notes": "Intermediate",
        "risk_notes": "Tight latency target",
        "source_job_uid": "2034153922546495276",
    }
    result = parse_requirement_analysis(payload)
    assert isinstance(result, RequirementAnalysis)
    assert result.technology_stack == ["Python", "FastAPI"]
    assert result.key_requirements == ["REST API", "SQLite"]
    assert result.budget_summary == "Hourly $10–$40"
    assert result.timeline_summary == "1–3 months"
    assert result.complexity_notes == "Intermediate"
    assert result.risk_notes == "Tight latency target"
    assert result.source_job_uid == "2034153922546495276"


def test_parse_requirement_analysis_json_string_happy_path() -> None:
    """S2-02: 合法 JSON 字符串 → 与 dict 等价。"""
    payload = {
        "technology_stack": ["Python"],
        "key_requirements": ["Batch processing"],
    }
    raw = json.dumps(payload, ensure_ascii=False)
    result = parse_requirement_analysis(raw)
    assert result.technology_stack == ["Python"]
    assert result.key_requirements == ["Batch processing"]


def test_parse_requirement_analysis_invalid_json_string() -> None:
    """S2-03: 非法 JSON → ValueError，消息可读。"""
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_requirement_analysis("{ not json")


def test_parse_requirement_analysis_validation_error_on_bad_type() -> None:
    """S2-04: 字段类型错误 → ValidationError。"""
    payload = {"technology_stack": "must be list", "key_requirements": []}
    with pytest.raises(ValidationError):
        parse_requirement_analysis(payload)


def test_parse_proposal_dict_happy_path() -> None:
    """S2-05: 合法 dict → Proposal。"""
    payload = {
        "title": "Experienced Python engineer for your automation",
        "body_markdown": "## Approach\n\nWe will use FastAPI.\n",
        "template_variables": {"client_name": "Acme"},
    }
    result = parse_proposal(payload)
    assert isinstance(result, Proposal)
    assert result.title == "Experienced Python engineer for your automation"
    assert "FastAPI" in result.body_markdown
    assert result.template_variables == {"client_name": "Acme"}


def test_parse_proposal_json_string_happy_path() -> None:
    """S2-06: 合法 JSON 字符串 → Proposal。"""
    payload = {"title": "Hi", "body_markdown": "Hello **world**"}
    result = parse_proposal(json.dumps(payload))
    assert result.title == "Hi"
    assert result.body_markdown == "Hello **world**"


def test_parse_proposal_empty_title_rejected() -> None:
    """S2-07: 标题为空 → ValidationError。"""
    with pytest.raises(ValidationError):
        parse_proposal({"title": "", "body_markdown": "x"})


def test_parse_proposal_json_root_not_object() -> None:
    """S2-08: JSON 根非 object → ValueError。"""
    with pytest.raises(ValueError, match="object"):
        parse_proposal('["only", "array"]')
