"""Story 3：SQLite DDL + aiosqlite 仓储插入/按 id 查询（内存库）."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nomadnomad.db import (
    AgentRunRepo,
    AppEventRepo,
    ProjectRepo,
    ProposalRepo,
    RequirementAnalysisRepo,
    connect_file,
    connect_memory,
    init_schema,
)
from nomadnomad.models import Proposal, RequirementAnalysis


@pytest.fixture
async def db_connection():
    """独立内存库，测试结束即销毁。"""
    async with connect_memory() as connection:
        await init_schema(connection)
        yield connection


@pytest.mark.asyncio
async def test_insert_then_get_by_id_round_trip_for_all_core_tables(db_connection) -> None:
    """插入 project / 分析 / 提案 / agent_run / app_event 后按 id 读出字段一致。"""
    project_id = await ProjectRepo.insert(
        db_connection,
        title="Demo Upwork gig",
        listing_html="<html>…</html>",
        listing_snapshot_json=json.dumps({"job_uid": "123", "title": "Demo"}, ensure_ascii=False),
    )
    loaded_project = await ProjectRepo.get_by_id(db_connection, project_id)
    assert loaded_project is not None
    assert loaded_project["id"] == project_id
    assert loaded_project["title"] == "Demo Upwork gig"
    assert loaded_project["listing_html"] == "<html>…</html>"
    assert json.loads(loaded_project["listing_snapshot_json"]) == {"job_uid": "123", "title": "Demo"}

    analysis = RequirementAnalysis(
        technology_stack=["Python"],
        key_requirements=["Do X"],
        budget_summary="$10–$40",
        source_job_uid="123",
    )
    analysis_id = await RequirementAnalysisRepo.insert(db_connection, project_id=project_id, analysis=analysis)
    loaded_analysis = await RequirementAnalysisRepo.get_by_id(db_connection, analysis_id)
    assert loaded_analysis is not None
    assert loaded_analysis["project_id"] == project_id
    assert json.loads(loaded_analysis["analysis_json"]) == analysis.model_dump()

    proposal = Proposal(title="Bid for 123", body_markdown="Hello **client**", template_variables={"k": "v"})
    proposal_id = await ProposalRepo.insert(db_connection, project_id=project_id, proposal=proposal)
    loaded_proposal = await ProposalRepo.get_by_id(db_connection, proposal_id)
    assert loaded_proposal is not None
    assert loaded_proposal["project_id"] == project_id
    assert json.loads(loaded_proposal["proposal_json"]) == proposal.model_dump()

    agent_run_id = await AgentRunRepo.insert(
        db_connection,
        project_id=project_id,
        agent_type="requirement_analyzer",
        input_payload_json=json.dumps({"prompt": "hi"}),
        output_payload_json=json.dumps({"ok": True}),
        success=True,
        duration_ms=42,
        error_message=None,
        trace_id="trace-abc",
    )
    loaded_run = await AgentRunRepo.get_by_id(db_connection, agent_run_id)
    assert loaded_run is not None
    assert loaded_run["project_id"] == project_id
    assert loaded_run["agent_type"] == "requirement_analyzer"
    assert loaded_run["success"] == 1
    assert loaded_run["duration_ms"] == 42
    assert loaded_run["trace_id"] == "trace-abc"
    assert json.loads(loaded_run["input_payload_json"]) == {"prompt": "hi"}

    event_id = await AppEventRepo.insert(
        db_connection,
        event_type="html_parse_completed",
        level="INFO",
        trace_id="trace-abc",
        project_id=project_id,
        source="ingest",
        payload_json=json.dumps({"bytes": 100}),
    )
    loaded_event = await AppEventRepo.get_by_id(db_connection, event_id)
    assert loaded_event is not None
    assert loaded_event["event_type"] == "html_parse_completed"
    assert loaded_event["level"] == "INFO"
    assert loaded_event["trace_id"] == "trace-abc"
    assert loaded_event["project_id"] == project_id
    assert loaded_event["source"] == "ingest"
    assert json.loads(loaded_event["payload_json"]) == {"bytes": 100}


@pytest.mark.asyncio
async def test_file_database_init_schema_is_idempotent(tmp_path: Path) -> None:
    """磁盘库：重复执行 init_schema 不报错（CREATE IF NOT EXISTS）。"""
    database_file = tmp_path / "nomad.sqlite"
    async with connect_file(database_file) as first_connection:
        await init_schema(first_connection)
    async with connect_file(database_file) as second_connection:
        await init_schema(second_connection)
        project_id = await ProjectRepo.insert(
            second_connection,
            title="file-backed",
            listing_html=None,
            listing_snapshot_json=None,
        )
        row = await ProjectRepo.get_by_id(second_connection, project_id)
    assert database_file.is_file()
    assert row is not None
    assert row["title"] == "file-backed"
