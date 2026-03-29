"""Story 4：需求分析 Agent — mock LLM 固定 JSON，校验 Schema 与 agent_runs 落库。"""

from __future__ import annotations

import json

import pytest

from nomadnomad.agents.requirement_analysis_agent import (
    REQUIREMENT_ANALYSIS_AGENT_TYPE,
    RequirementAnalysisAgentOutcome,
    run_requirement_analysis_agent,
)
from nomadnomad.db import AgentRunRepo, ProjectInsertPayload, ProjectRepo, connect_memory, init_schema
from nomadnomad.models import JobPostingSnapshot


class RecordingFakeJsonClient:
    """按顺序返回预设 JSON 字符串，并记录调用参数。"""

    def __init__(self, response_bodies: list[str]) -> None:
        self.response_bodies = response_bodies
        self.call_index = 0
        self.system_prompts: list[str] = []
        self.user_prompts: list[str] = []

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        self.system_prompts.append(system_prompt)
        self.user_prompts.append(user_prompt)
        body = self.response_bodies[self.call_index]
        self.call_index += 1
        return body


def _minimal_snapshot() -> JobPostingSnapshot:
    return JobPostingSnapshot(
        job_uid="2034153922546495276",
        title="Automated Image Solving",
        summary_text="Build a Python-based system with low latency.",
        mandatory_skills=["Python", "Automation"],
    )


VALID_ANALYSIS_JSON = json.dumps(
    {
        "technology_stack": ["Python"],
        "key_requirements": ["Deliver low-latency automation"],
        "budget_summary": "$10–$40 hourly",
        "timeline_summary": "1–3 months",
        "complexity_notes": "Intermediate",
        "risk_notes": "50+ proposals",
        "source_job_uid": "2034153922546495276",
    },
    ensure_ascii=False,
)


@pytest.fixture
async def db_connection():
    async with connect_memory() as connection:
        await init_schema(connection)
        yield connection


@pytest.mark.asyncio
async def test_requirement_analysis_agent_success_writes_agent_run(
    db_connection,
) -> None:
    """S4-01：mock LLM 返回合法 JSON → RequirementAnalysis 与 agent_runs 成功行一致。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p1", listing_html=None, listing_snapshot_json=None),
    )
    fake_llm = RecordingFakeJsonClient([VALID_ANALYSIS_JSON])
    snapshot = _minimal_snapshot()

    outcome = await run_requirement_analysis_agent(
        db_connection,
        project_id=project_id,
        snapshot=snapshot,
        llm_client=fake_llm,
        trace_id="trace-s4-01",
    )
    assert isinstance(outcome, RequirementAnalysisAgentOutcome)
    assert outcome.error_message is None
    assert outcome.analysis is not None
    assert outcome.analysis.source_job_uid == "2034153922546495276"
    assert "Python" in outcome.analysis.technology_stack

    loaded = await AgentRunRepo.get_by_id(db_connection, outcome.agent_run_id)
    assert loaded is not None
    assert loaded["project_id"] == project_id
    assert loaded["agent_type"] == REQUIREMENT_ANALYSIS_AGENT_TYPE
    assert loaded["success"] == 1
    assert loaded["trace_id"] == "trace-s4-01"
    assert loaded["error_message"] is None
    assert loaded["duration_ms"] is not None
    assert loaded["input_payload_json"] is not None
    assert "2034153922546495276" in loaded["input_payload_json"]
    assert loaded["output_payload_json"] is not None
    assert json.loads(loaded["output_payload_json"]) == outcome.analysis.model_dump()


@pytest.mark.asyncio
async def test_requirement_analysis_agent_invalid_llm_json_records_failure(
    db_connection,
) -> None:
    """S4-02：LLM 返回无法解析为 RequirementAnalysis 的内容 → success=0 且 error_message 非空。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p2", listing_html=None, listing_snapshot_json=None),
    )
    bad_payload = json.dumps({"technology_stack": "must_be_a_list_not_string"})
    fake_llm = RecordingFakeJsonClient([bad_payload, bad_payload])

    outcome = await run_requirement_analysis_agent(
        db_connection,
        project_id=project_id,
        normalized_job_text="Some job text only.",
        llm_client=fake_llm,
        trace_id="trace-s4-02",
    )
    assert outcome.analysis is None
    assert outcome.error_message is not None

    loaded = await AgentRunRepo.get_by_id(db_connection, outcome.agent_run_id)
    assert loaded is not None
    assert loaded["success"] == 0
    assert loaded["error_message"] is not None


@pytest.mark.asyncio
async def test_requirement_analysis_agent_rejects_ambiguous_inputs(db_connection) -> None:
    """S4-05：同时提供 snapshot 与 normalized_job_text → ValueError（不写 agent_run）。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p4", listing_html=None, listing_snapshot_json=None),
    )

    with pytest.raises(ValueError, match="exactly one"):
        await run_requirement_analysis_agent(
            db_connection,
            project_id=project_id,
            snapshot=_minimal_snapshot(),
            normalized_job_text="duplicate",
            llm_client=RecordingFakeJsonClient([VALID_ANALYSIS_JSON]),
        )


@pytest.mark.asyncio
async def test_requirement_analysis_agent_retries_once_after_parse_failure(
    db_connection,
) -> None:
    """S4-03：首次返回非法 JSON、第二次返回合法 → 最终成功且 agent_run 记录成功。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        row_to_insert=ProjectInsertPayload(title="p3", listing_html=None, listing_snapshot_json=None),
    )
    fake_llm = RecordingFakeJsonClient(["not-json-at-all", VALID_ANALYSIS_JSON])

    outcome = await run_requirement_analysis_agent(
        db_connection,
        project_id=project_id,
        snapshot=_minimal_snapshot(),
        llm_client=fake_llm,
        trace_id="trace-s4-03",
    )
    assert outcome.analysis is not None
    assert outcome.error_message is None
    assert fake_llm.call_index == 2

    loaded = await AgentRunRepo.get_by_id(db_connection, outcome.agent_run_id)
    assert loaded is not None
    assert loaded["success"] == 1
