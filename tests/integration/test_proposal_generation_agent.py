"""Story 5：提案生成 Agent — mock LLM 固定 JSON，校验 Proposal 与 agent_runs 落库。"""

from __future__ import annotations

import json

import pytest

from nomadnomad.agents.proposal_generation_agent import (
    PROPOSAL_GENERATION_AGENT_TYPE,
    ProposalGenerationAgentOutcome,
    run_proposal_generation_agent,
)
from nomadnomad.db import (
    AgentRunRepo,
    ProjectInsertPayload,
    ProjectRepo,
    RequirementAnalysisRepo,
    connect_memory,
    init_schema,
)
from nomadnomad.models import RequirementAnalysis
from nomadnomad.preview import RecordingSequentialJsonClient


def _minimal_analysis() -> RequirementAnalysis:
    return RequirementAnalysis(
        technology_stack=["Python"],
        key_requirements=["Low latency"],
        budget_summary="$10–$40 hourly",
        timeline_summary="1–3 months",
        source_job_uid="2034153922546495276",
    )


VALID_PROPOSAL_JSON = json.dumps(
    {
        "title": "Experienced Python automation for your pipeline",
        "body_markdown": "## Approach\n\nI will use **Python** with async I/O.\n\nThanks.",
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
async def test_proposal_generation_agent_success_writes_agent_run(db_connection) -> None:
    """S5-01：mock LLM 返回合法 JSON → Proposal 与 agent_runs 成功行一致。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p1", listing_html=None, listing_snapshot_json=None),
    )
    fake_llm = RecordingSequentialJsonClient([VALID_PROPOSAL_JSON])
    analysis = _minimal_analysis()

    outcome = await run_proposal_generation_agent(
        db_connection,
        project_id=project_id,
        requirement_analysis=analysis,
        llm_client=fake_llm,
        trace_id="trace-s5-01",
    )
    assert isinstance(outcome, ProposalGenerationAgentOutcome)
    assert outcome.error_message is None
    assert outcome.proposal is not None
    assert "Python" in outcome.proposal.body_markdown

    loaded = await AgentRunRepo.get_by_id(db_connection, outcome.agent_run_id)
    assert loaded is not None
    assert loaded["project_id"] == project_id
    assert loaded["agent_type"] == PROPOSAL_GENERATION_AGENT_TYPE
    assert loaded["success"] == 1
    assert loaded["trace_id"] == "trace-s5-01"
    assert loaded["error_message"] is None
    assert loaded["duration_ms"] is not None
    assert loaded["input_payload_json"] is not None
    assert "2034153922546495276" in loaded["input_payload_json"]
    assert loaded["output_payload_json"] is not None
    assert json.loads(loaded["output_payload_json"]) == outcome.proposal.model_dump()


@pytest.mark.asyncio
async def test_proposal_generation_agent_invalid_llm_json_records_failure(db_connection) -> None:
    """S5-02：LLM 返回无法解析为 Proposal 的内容 → success=0 且 error_message 非空。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p2", listing_html=None, listing_snapshot_json=None),
    )
    bad_payload = json.dumps({"title": "", "body_markdown": "x"})
    fake_llm = RecordingSequentialJsonClient([bad_payload, bad_payload])

    outcome = await run_proposal_generation_agent(
        db_connection,
        project_id=project_id,
        requirement_analysis=_minimal_analysis(),
        llm_client=fake_llm,
        trace_id="trace-s5-02",
    )
    assert outcome.proposal is None
    assert outcome.error_message is not None

    loaded = await AgentRunRepo.get_by_id(db_connection, outcome.agent_run_id)
    assert loaded is not None
    assert loaded["success"] == 0
    assert loaded["error_message"] is not None


@pytest.mark.asyncio
async def test_proposal_generation_agent_rejects_ambiguous_inputs(db_connection) -> None:
    """S5-05：同时提供 analysis 与 requirement_analysis_id → ValueError（不写 agent_run）。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p4", listing_html=None, listing_snapshot_json=None),
    )
    analysis_id = await RequirementAnalysisRepo.insert(
        db_connection,
        project_id=project_id,
        analysis=_minimal_analysis(),
    )

    with pytest.raises(ValueError, match="exactly one"):
        await run_proposal_generation_agent(
            db_connection,
            project_id=project_id,
            requirement_analysis=_minimal_analysis(),
            requirement_analysis_id=analysis_id,
            llm_client=RecordingSequentialJsonClient([VALID_PROPOSAL_JSON]),
        )


@pytest.mark.asyncio
async def test_proposal_generation_agent_rejects_missing_inputs(db_connection) -> None:
    """S5-06：未提供 analysis 与 id → ValueError（不写 agent_run）。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p5", listing_html=None, listing_snapshot_json=None),
    )

    with pytest.raises(ValueError, match="exactly one"):
        await run_proposal_generation_agent(
            db_connection,
            project_id=project_id,
            llm_client=RecordingSequentialJsonClient([VALID_PROPOSAL_JSON]),
        )


@pytest.mark.asyncio
async def test_proposal_generation_agent_not_found_analysis_id(db_connection) -> None:
    """S5-07：不存在的 requirement_analysis_id → ValueError（不写 agent_run）。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p6", listing_html=None, listing_snapshot_json=None),
    )

    with pytest.raises(ValueError, match="not found"):
        await run_proposal_generation_agent(
            db_connection,
            project_id=project_id,
            requirement_analysis_id=999_999,
            llm_client=RecordingSequentialJsonClient([VALID_PROPOSAL_JSON]),
        )


@pytest.mark.asyncio
async def test_proposal_generation_agent_retries_once_after_parse_failure(db_connection) -> None:
    """S5-03：首次返回非法、第二次返回合法 → 最终成功且 agent_run 记录成功。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p3", listing_html=None, listing_snapshot_json=None),
    )
    fake_llm = RecordingSequentialJsonClient(["not-json-at-all", VALID_PROPOSAL_JSON])

    outcome = await run_proposal_generation_agent(
        db_connection,
        project_id=project_id,
        requirement_analysis=_minimal_analysis(),
        llm_client=fake_llm,
        trace_id="trace-s5-03",
    )
    assert outcome.proposal is not None
    assert outcome.error_message is None
    assert fake_llm.call_index == 2

    loaded = await AgentRunRepo.get_by_id(db_connection, outcome.agent_run_id)
    assert loaded is not None
    assert loaded["success"] == 1


@pytest.mark.asyncio
async def test_proposal_generation_agent_loads_analysis_by_id(db_connection) -> None:
    """S5-04：仅传 requirement_analysis_id → 从库加载并生成 Proposal。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p7", listing_html=None, listing_snapshot_json=None),
    )
    analysis_id = await RequirementAnalysisRepo.insert(
        db_connection,
        project_id=project_id,
        analysis=_minimal_analysis(),
    )
    fake_llm = RecordingSequentialJsonClient([VALID_PROPOSAL_JSON])

    outcome = await run_proposal_generation_agent(
        db_connection,
        project_id=project_id,
        requirement_analysis_id=analysis_id,
        llm_client=fake_llm,
        trace_id="trace-s5-04",
    )
    assert outcome.proposal is not None
    assert outcome.proposal.title.startswith("Experienced")

    loaded = await AgentRunRepo.get_by_id(db_connection, outcome.agent_run_id)
    assert loaded is not None
    payload = json.loads(loaded["input_payload_json"])
    assert payload.get("requirement_analysis_id") == analysis_id
    assert "requirement_analysis" in payload
