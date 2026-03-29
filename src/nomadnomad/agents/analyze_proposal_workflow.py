"""Story 6：LangGraph 编排「需求分析 → 提案生成」，并写入 ``requirement_analyses`` / ``proposals``。"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

import aiosqlite
from langgraph.graph import END, START, StateGraph
from loguru import logger
from pydantic.dataclasses import dataclass

from nomadnomad.agents.llm.json_chat_client import JsonCompletionClient
from nomadnomad.agents.proposal_generation_agent import (
    PROPOSAL_GENERATION_AGENT_TYPE,
    run_proposal_generation_agent,
)
from nomadnomad.agents.requirement_analysis_agent import (
    REQUIREMENT_ANALYSIS_AGENT_TYPE,
    run_requirement_analysis_agent,
)
from nomadnomad.db.insert_payloads import ProjectInsertPayload
from nomadnomad.db.repositories import ProjectRepo, ProposalRepo, RequirementAnalysisRepo
from nomadnomad.ingest import parse_upwork_job_html
from nomadnomad.models import JobPostingSnapshot

WORKFLOW_GRAPH_NAME = "analyze_and_propose"


class AnalyzeProposalGraphState(TypedDict, total=False):
    """LangGraph 状态：两节点共享 ``project_id`` 与 ``snapshot``。"""

    project_id: int
    snapshot: JobPostingSnapshot
    trace_id: str | None
    requirement_analysis_id: int | None
    proposal_id: int | None
    workflow_error: str | None
    requirement_analysis_agent_run_id: int | None
    proposal_generation_agent_run_id: int | None


@dataclass
class AnalyzeProposalWorkflowOutcome:
    """编排结束后的对外结果。"""

    project_id: int
    requirement_analysis_id: int | None
    proposal_id: int | None
    status: Literal["success", "failed_analysis", "failed_proposal"]
    error_message: str | None
    requirement_analysis_agent_run_id: int | None = None
    proposal_generation_agent_run_id: int | None = None


def _validate_exactly_one_job_source(
    *,
    listing_html: str | None,
    job_posting_snapshot: JobPostingSnapshot | None,
    project_id: int | None,
) -> None:
    provided = sum(1 for candidate in (listing_html, job_posting_snapshot, project_id) if candidate is not None)
    if provided != 1:
        raise ValueError(
            "Provide exactly one of listing_html=, job_posting_snapshot=, or project_id=",
        )


async def _resolve_project_and_snapshot(
    connection: aiosqlite.Connection,
    *,
    listing_html: str | None,
    job_posting_snapshot: JobPostingSnapshot | None,
    project_id: int | None,
) -> tuple[int, JobPostingSnapshot]:
    _validate_exactly_one_job_source(
        listing_html=listing_html,
        job_posting_snapshot=job_posting_snapshot,
        project_id=project_id,
    )
    if project_id is not None:
        row = await ProjectRepo.get_by_id(connection, project_id)
        if row is None:
            raise ValueError(f"project_id={project_id} not found")
        raw_snapshot = row["listing_snapshot_json"]
        if not raw_snapshot:
            raise ValueError(f"project_id={project_id} has no listing_snapshot_json")
        return project_id, JobPostingSnapshot.model_validate_json(raw_snapshot)
    if listing_html is not None:
        snapshot = parse_upwork_job_html(listing_html)
        new_project_id = await ProjectRepo.insert(
            connection,
            row_to_insert=ProjectInsertPayload(
                title=snapshot.title or "nomadnomad-job",
                listing_html=listing_html,
                listing_snapshot_json=snapshot.model_dump_json(),
            ),
        )
        return new_project_id, snapshot
    assert job_posting_snapshot is not None
    snapshot = job_posting_snapshot
    new_project_id = await ProjectRepo.insert(
        connection,
        row_to_insert=ProjectInsertPayload(
            title=snapshot.title or "nomadnomad-job",
            listing_html=None,
            listing_snapshot_json=snapshot.model_dump_json(),
        ),
    )
    return new_project_id, snapshot


def _route_after_requirement_analysis(state: AnalyzeProposalGraphState) -> str:
    if state.get("workflow_error"):
        return END
    return "proposal_generation"


def _outcome_from_final_state(
    final_state: AnalyzeProposalGraphState,
) -> AnalyzeProposalWorkflowOutcome:
    project_id = final_state["project_id"]
    proposal_id = final_state.get("proposal_id")
    requirement_analysis_id = final_state.get("requirement_analysis_id")
    err = final_state.get("workflow_error")
    ra_run = final_state.get("requirement_analysis_agent_run_id")
    prop_run = final_state.get("proposal_generation_agent_run_id")

    if proposal_id is not None:
        return AnalyzeProposalWorkflowOutcome(
            project_id=project_id,
            requirement_analysis_id=requirement_analysis_id,
            proposal_id=proposal_id,
            status="success",
            error_message=None,
            requirement_analysis_agent_run_id=ra_run,
            proposal_generation_agent_run_id=prop_run,
        )
    if requirement_analysis_id is None:
        return AnalyzeProposalWorkflowOutcome(
            project_id=project_id,
            requirement_analysis_id=None,
            proposal_id=None,
            status="failed_analysis",
            error_message=err,
            requirement_analysis_agent_run_id=ra_run,
            proposal_generation_agent_run_id=prop_run,
        )
    return AnalyzeProposalWorkflowOutcome(
        project_id=project_id,
        requirement_analysis_id=requirement_analysis_id,
        proposal_id=None,
        status="failed_proposal",
        error_message=err,
        requirement_analysis_agent_run_id=ra_run,
        proposal_generation_agent_run_id=prop_run,
    )


def build_analyze_proposal_graph(
    connection: aiosqlite.Connection,
    llm_client: JsonCompletionClient,
) -> Any:
    """构建「需求分析 → 提案生成」编译图（闭包捕获 ``connection`` 与 ``llm_client``）。"""

    async def requirement_analysis_node(state: AnalyzeProposalGraphState) -> dict[str, Any]:
        outcome = await run_requirement_analysis_agent(
            connection,
            project_id=state["project_id"],
            snapshot=state["snapshot"],
            llm_client=llm_client,
            trace_id=state.get("trace_id"),
        )
        if outcome.analysis is None:
            return {
                "workflow_error": outcome.error_message or "requirement_analysis_failed",
                "requirement_analysis_agent_run_id": outcome.agent_run_id,
            }
        analysis_row_id = await RequirementAnalysisRepo.insert(
            connection,
            project_id=state["project_id"],
            analysis=outcome.analysis,
        )
        return {
            "requirement_analysis_id": analysis_row_id,
            "requirement_analysis_agent_run_id": outcome.agent_run_id,
        }

    async def proposal_generation_node(state: AnalyzeProposalGraphState) -> dict[str, Any]:
        requirement_analysis_id = state.get("requirement_analysis_id")
        if requirement_analysis_id is None:
            return {
                "workflow_error": state.get("workflow_error") or "missing_requirement_analysis_id",
            }
        outcome = await run_proposal_generation_agent(
            connection,
            project_id=state["project_id"],
            requirement_analysis_id=requirement_analysis_id,
            llm_client=llm_client,
            trace_id=state.get("trace_id"),
        )
        if outcome.proposal is None:
            return {
                "workflow_error": outcome.error_message or "proposal_generation_failed",
                "proposal_generation_agent_run_id": outcome.agent_run_id,
            }
        proposal_row_id = await ProposalRepo.insert(
            connection,
            project_id=state["project_id"],
            proposal=outcome.proposal,
        )
        return {
            "proposal_id": proposal_row_id,
            "proposal_generation_agent_run_id": outcome.agent_run_id,
        }

    builder = StateGraph(AnalyzeProposalGraphState)
    builder.add_node("requirement_analysis", requirement_analysis_node)
    builder.add_node("proposal_generation", proposal_generation_node)
    builder.add_edge(START, "requirement_analysis")
    builder.add_conditional_edges(
        "requirement_analysis",
        _route_after_requirement_analysis,
        {END: END, "proposal_generation": "proposal_generation"},
    )
    builder.add_edge("proposal_generation", END)
    return builder.compile(name=WORKFLOW_GRAPH_NAME)


async def run_analyze_proposal_workflow(
    connection: aiosqlite.Connection,
    *,
    llm_client: JsonCompletionClient,
    trace_id: str | None = None,
    listing_html: str | None = None,
    job_posting_snapshot: JobPostingSnapshot | None = None,
    project_id: int | None = None,
) -> AnalyzeProposalWorkflowOutcome:
    """解析/加载快照后，经 LangGraph 执行分析 → 提案并落库。"""
    resolved_project_id, snapshot = await _resolve_project_and_snapshot(
        connection,
        listing_html=listing_html,
        job_posting_snapshot=job_posting_snapshot,
        project_id=project_id,
    )
    log = logger.bind(
        project_id=resolved_project_id,
        trace_id=trace_id,
        workflow=WORKFLOW_GRAPH_NAME,
    )
    log.info("analyze_proposal_workflow_started")

    initial: AnalyzeProposalGraphState = {
        "project_id": resolved_project_id,
        "snapshot": snapshot,
        "trace_id": trace_id,
    }
    graph = build_analyze_proposal_graph(connection, llm_client)
    final_state = await graph.ainvoke(initial)
    outcome = _outcome_from_final_state(final_state)
    log.info(
        "analyze_proposal_workflow_finished",
        status=outcome.status,
        requirement_analysis_id=outcome.requirement_analysis_id,
        proposal_id=outcome.proposal_id,
    )
    return outcome


def agent_types_for_success_path() -> tuple[str, str]:
    """测试与文档用：成功路径上两条 ``agent_runs`` 的 ``agent_type`` 顺序。"""
    return (REQUIREMENT_ANALYSIS_AGENT_TYPE, PROPOSAL_GENERATION_AGENT_TYPE)
