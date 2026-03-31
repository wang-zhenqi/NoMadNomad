"""Story 6：LangGraph「分析 → 提案」编排 — mock LLM，校验落库与 agent_runs 类型。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nomadnomad.agents.analyze_proposal_workflow import (
    AnalyzeProposalWorkflowOutcome,
    agent_types_for_success_path,
    run_analyze_proposal_workflow,
)
from nomadnomad.agents.proposal_generation_agent import PROPOSAL_GENERATION_AGENT_TYPE
from nomadnomad.agents.requirement_analysis_agent import REQUIREMENT_ANALYSIS_AGENT_TYPE
from nomadnomad.db import (
    AgentRunRepo,
    ProjectInsertPayload,
    ProjectRepo,
    ProposalRepo,
    RequirementAnalysisRepo,
    connect_memory,
    init_schema,
)
from nomadnomad.ingest import parse_upwork_job_html
from nomadnomad.models import RequirementAnalysis
from nomadnomad.preview import RecordingSequentialJsonClient


def _demo_html_path() -> Path:
    return Path(__file__).resolve().parents[2] / "resources" / "demo" / "demo_requirement.html"


VALID_ANALYSIS_JSON = json.dumps(
    {
        "technology_stack": ["Python"],
        "key_requirements": ["Low latency"],
        "budget_summary": "$10–$40 hourly",
        "timeline_summary": "1–3 months",
        "complexity_notes": None,
        "risk_notes": None,
        "source_job_uid": "2034153922546495276",
    },
    ensure_ascii=False,
)

VALID_PROPOSAL_JSON = json.dumps(
    {
        "title": "Experienced Python automation",
        "body_markdown": "## Approach\n\nI will use **Python**.\n\nThanks.",
        "template_variables": {"client_name": "there"},
    },
    ensure_ascii=False,
)


@pytest.fixture
async def db_connection():
    async with connect_memory() as connection:
        await init_schema(connection)
        yield connection


@pytest.mark.asyncio
async def test_workflow_html_to_proposal_success_persists_rows_and_agent_types(db_connection) -> None:
    """S6-01：HTML 入口 → 双表落库；两条 agent_runs 类型正确。"""
    raw_html = _demo_html_path().read_text(encoding="utf-8")
    fake_llm = RecordingSequentialJsonClient([VALID_ANALYSIS_JSON, VALID_PROPOSAL_JSON])

    outcome = await run_analyze_proposal_workflow(
        db_connection,
        llm_client=fake_llm,
        listing_html=raw_html,
        trace_id="trace-s6-01",
    )
    assert isinstance(outcome, AnalyzeProposalWorkflowOutcome)
    assert outcome.status == "success"
    assert outcome.error_message is None
    assert outcome.project_id is not None
    assert outcome.requirement_analysis_id is not None
    assert outcome.proposal_id is not None
    assert outcome.requirement_analysis_agent_run_id is not None
    assert outcome.proposal_generation_agent_run_id is not None

    ra_row = await RequirementAnalysisRepo.get_by_id(db_connection, outcome.requirement_analysis_id)
    assert ra_row is not None
    assert ra_row["project_id"] == outcome.project_id

    prop_row = await ProposalRepo.get_by_id(db_connection, outcome.proposal_id)
    assert prop_row is not None
    assert prop_row["project_id"] == outcome.project_id

    ra_run = await AgentRunRepo.get_by_id(db_connection, outcome.requirement_analysis_agent_run_id)
    prop_run = await AgentRunRepo.get_by_id(db_connection, outcome.proposal_generation_agent_run_id)
    assert ra_run is not None
    assert prop_run is not None
    assert ra_run["agent_type"] == REQUIREMENT_ANALYSIS_AGENT_TYPE
    assert prop_run["agent_type"] == PROPOSAL_GENERATION_AGENT_TYPE
    assert agent_types_for_success_path() == (
        REQUIREMENT_ANALYSIS_AGENT_TYPE,
        PROPOSAL_GENERATION_AGENT_TYPE,
    )


@pytest.mark.asyncio
async def test_workflow_analysis_failure_skips_proposal_and_requirement_analysis_table(db_connection) -> None:
    """S6-02：分析失败 → 无 requirement_analyses / proposals；不调用第二次节点。"""
    raw_html = _demo_html_path().read_text(encoding="utf-8")
    # 非法 Schema：technology_stack 必须为 list[str]，无法用 extra=ignore 绕过
    bad = json.dumps({"technology_stack": "not_a_list"})
    fake_llm = RecordingSequentialJsonClient([bad, bad])

    outcome = await run_analyze_proposal_workflow(
        db_connection,
        llm_client=fake_llm,
        listing_html=raw_html,
        trace_id="trace-s6-02",
    )
    assert outcome.status == "failed_analysis"
    assert outcome.requirement_analysis_id is None
    assert outcome.proposal_id is None
    assert outcome.error_message is not None
    assert fake_llm.call_index == 2


@pytest.mark.asyncio
async def test_workflow_from_job_posting_snapshot_success(db_connection) -> None:
    """S6-03：仅传快照 → 成功落库。"""
    raw_html = _demo_html_path().read_text(encoding="utf-8")
    snapshot = parse_upwork_job_html(raw_html)
    fake_llm = RecordingSequentialJsonClient([VALID_ANALYSIS_JSON, VALID_PROPOSAL_JSON])

    outcome = await run_analyze_proposal_workflow(
        db_connection,
        llm_client=fake_llm,
        job_posting_snapshot=snapshot,
        trace_id="trace-s6-03",
    )
    assert outcome.status == "success"
    assert outcome.requirement_analysis_id is not None
    assert outcome.proposal_id is not None


@pytest.mark.asyncio
async def test_workflow_from_existing_project_id_success(db_connection) -> None:
    """S6-04：已有 project + listing_snapshot_json → 成功。"""
    raw_html = _demo_html_path().read_text(encoding="utf-8")
    snapshot = parse_upwork_job_html(raw_html)
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(
            title=snapshot.title or "p",
            listing_html=None,
            listing_snapshot_json=snapshot.model_dump_json(),
        ),
    )
    fake_llm = RecordingSequentialJsonClient([VALID_ANALYSIS_JSON, VALID_PROPOSAL_JSON])

    outcome = await run_analyze_proposal_workflow(
        db_connection,
        llm_client=fake_llm,
        project_id=project_id,
        trace_id="trace-s6-04",
    )
    assert outcome.status == "success"
    assert outcome.project_id == project_id
    assert outcome.proposal_id is not None


@pytest.mark.asyncio
async def test_workflow_rejects_multiple_input_sources(db_connection) -> None:
    """S6-05：多源输入 → ValueError。"""
    raw_html = _demo_html_path().read_text(encoding="utf-8")
    snapshot = parse_upwork_job_html(raw_html)
    fake_llm = RecordingSequentialJsonClient([VALID_ANALYSIS_JSON, VALID_PROPOSAL_JSON])

    with pytest.raises(ValueError, match="exactly one"):
        await run_analyze_proposal_workflow(
            db_connection,
            llm_client=fake_llm,
            listing_html=raw_html,
            job_posting_snapshot=snapshot,
        )


@pytest.mark.asyncio
async def test_workflow_proposal_failure_after_analysis_persists_requirement_analysis_only(db_connection) -> None:
    """S6-06：分析成功、提案失败 → requirement_analyses 有行，无 proposals。"""
    raw_html = _demo_html_path().read_text(encoding="utf-8")
    bad_proposal = json.dumps({"title": "", "body_markdown": "x"})
    fake_llm = RecordingSequentialJsonClient([VALID_ANALYSIS_JSON, bad_proposal, bad_proposal])

    outcome = await run_analyze_proposal_workflow(
        db_connection,
        llm_client=fake_llm,
        listing_html=raw_html,
        trace_id="trace-s6-06",
    )
    assert outcome.status == "failed_proposal"
    assert outcome.requirement_analysis_id is not None
    assert outcome.proposal_id is None
    assert outcome.error_message is not None

    ra_row = await RequirementAnalysisRepo.get_by_id(db_connection, outcome.requirement_analysis_id)
    assert ra_row is not None
    parsed = RequirementAnalysis.model_validate_json(ra_row["analysis_json"])
    assert "Python" in parsed.technology_stack
