"""Story 6：LangGraph 编排「需求分析 → 提案生成」，并写入 ``requirement_analyses`` / ``proposals``。"""

from __future__ import annotations

from typing import Any, Final, Literal, TypedDict

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
from nomadnomad.models import JobPostingSnapshot
from nomadnomad.services.analyze_proposal_use_case import (
    persist_proposal,
    persist_requirement_analysis,
    resolve_project_and_snapshot,
)

WORKFLOW_GRAPH_NAME = "analyze_and_propose"

WorkflowOutcomeStatus = Literal["success", "failed_analysis", "failed_proposal"]

WORKFLOW_STATUS_SUCCESS: Final[WorkflowOutcomeStatus] = "success"
WORKFLOW_STATUS_FAILED_ANALYSIS: Final[WorkflowOutcomeStatus] = "failed_analysis"
WORKFLOW_STATUS_FAILED_PROPOSAL: Final[WorkflowOutcomeStatus] = "failed_proposal"

WORKFLOW_ERROR_REQUIREMENT_ANALYSIS_FAILED: Final[str] = "requirement_analysis_failed"
WORKFLOW_ERROR_PROPOSAL_GENERATION_FAILED: Final[str] = "proposal_generation_failed"
WORKFLOW_ERROR_MISSING_REQUIREMENT_ANALYSIS_ID: Final[str] = "missing_requirement_analysis_id"

NODE_REQUIREMENT_ANALYSIS: Final[Literal["requirement_analysis"]] = "requirement_analysis"
NODE_PROPOSAL_GENERATION: Final[Literal["proposal_generation"]] = "proposal_generation"

STATE_PROJECT_ID: Final[Literal["project_id"]] = "project_id"
STATE_SNAPSHOT: Final[Literal["snapshot"]] = "snapshot"
STATE_TRACE_ID: Final[Literal["trace_id"]] = "trace_id"
STATE_REQUIREMENT_ANALYSIS_ID: Final[Literal["requirement_analysis_id"]] = "requirement_analysis_id"
STATE_PROPOSAL_ID: Final[Literal["proposal_id"]] = "proposal_id"
STATE_WORKFLOW_ERROR: Final[Literal["workflow_error"]] = "workflow_error"
STATE_REQUIREMENT_ANALYSIS_AGENT_RUN_ID: Final[Literal["requirement_analysis_agent_run_id"]] = (
    "requirement_analysis_agent_run_id"
)
STATE_PROPOSAL_GENERATION_AGENT_RUN_ID: Final[Literal["proposal_generation_agent_run_id"]] = (
    "proposal_generation_agent_run_id"
)


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


def _route_after_requirement_analysis(state: AnalyzeProposalGraphState) -> str:
    if state.get(STATE_WORKFLOW_ERROR):
        return END
    return NODE_PROPOSAL_GENERATION


def _outcome_from_final_state(
    final_state: AnalyzeProposalGraphState,
) -> AnalyzeProposalWorkflowOutcome:
    project_id = final_state[STATE_PROJECT_ID]
    proposal_id = final_state.get(STATE_PROPOSAL_ID)
    requirement_analysis_id = final_state.get(STATE_REQUIREMENT_ANALYSIS_ID)
    err = final_state.get(STATE_WORKFLOW_ERROR)
    ra_run = final_state.get(STATE_REQUIREMENT_ANALYSIS_AGENT_RUN_ID)
    prop_run = final_state.get(STATE_PROPOSAL_GENERATION_AGENT_RUN_ID)

    if proposal_id is not None:
        return AnalyzeProposalWorkflowOutcome(
            project_id=project_id,
            requirement_analysis_id=requirement_analysis_id,
            proposal_id=proposal_id,
            status=WORKFLOW_STATUS_SUCCESS,
            error_message=None,
            requirement_analysis_agent_run_id=ra_run,
            proposal_generation_agent_run_id=prop_run,
        )
    if requirement_analysis_id is None:
        return AnalyzeProposalWorkflowOutcome(
            project_id=project_id,
            requirement_analysis_id=None,
            proposal_id=None,
            status=WORKFLOW_STATUS_FAILED_ANALYSIS,
            error_message=err,
            requirement_analysis_agent_run_id=ra_run,
            proposal_generation_agent_run_id=prop_run,
        )
    return AnalyzeProposalWorkflowOutcome(
        project_id=project_id,
        requirement_analysis_id=requirement_analysis_id,
        proposal_id=None,
        status=WORKFLOW_STATUS_FAILED_PROPOSAL,
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
            project_id=state[STATE_PROJECT_ID],
            snapshot=state[STATE_SNAPSHOT],
            llm_client=llm_client,
            trace_id=state.get(STATE_TRACE_ID),
        )
        if outcome.analysis is None:
            return {
                STATE_WORKFLOW_ERROR: outcome.error_message or WORKFLOW_ERROR_REQUIREMENT_ANALYSIS_FAILED,
                STATE_REQUIREMENT_ANALYSIS_AGENT_RUN_ID: outcome.agent_run_id,
            }
        analysis_row_id = await persist_requirement_analysis(
            connection,
            project_id=state[STATE_PROJECT_ID],
            analysis=outcome.analysis,
        )
        return {
            STATE_REQUIREMENT_ANALYSIS_ID: analysis_row_id,
            STATE_REQUIREMENT_ANALYSIS_AGENT_RUN_ID: outcome.agent_run_id,
        }

    async def proposal_generation_node(state: AnalyzeProposalGraphState) -> dict[str, Any]:
        requirement_analysis_id = state.get(STATE_REQUIREMENT_ANALYSIS_ID)
        if requirement_analysis_id is None:
            return {
                STATE_WORKFLOW_ERROR: state.get(STATE_WORKFLOW_ERROR) or WORKFLOW_ERROR_MISSING_REQUIREMENT_ANALYSIS_ID,
            }
        outcome = await run_proposal_generation_agent(
            connection,
            project_id=state[STATE_PROJECT_ID],
            requirement_analysis_id=requirement_analysis_id,
            llm_client=llm_client,
            trace_id=state.get(STATE_TRACE_ID),
        )
        if outcome.proposal is None:
            return {
                STATE_WORKFLOW_ERROR: outcome.error_message or WORKFLOW_ERROR_PROPOSAL_GENERATION_FAILED,
                STATE_PROPOSAL_GENERATION_AGENT_RUN_ID: outcome.agent_run_id,
            }
        proposal_row_id = await persist_proposal(
            connection,
            project_id=state[STATE_PROJECT_ID],
            proposal=outcome.proposal,
        )
        return {
            STATE_PROPOSAL_ID: proposal_row_id,
            STATE_PROPOSAL_GENERATION_AGENT_RUN_ID: outcome.agent_run_id,
        }

    builder = StateGraph(AnalyzeProposalGraphState)
    builder.add_node(NODE_REQUIREMENT_ANALYSIS, requirement_analysis_node)
    builder.add_node(NODE_PROPOSAL_GENERATION, proposal_generation_node)
    builder.add_edge(START, NODE_REQUIREMENT_ANALYSIS)
    builder.add_conditional_edges(
        NODE_REQUIREMENT_ANALYSIS,
        _route_after_requirement_analysis,
        {END: END, NODE_PROPOSAL_GENERATION: NODE_PROPOSAL_GENERATION},
    )
    builder.add_edge(NODE_PROPOSAL_GENERATION, END)
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
    resolved_project_id, snapshot = await resolve_project_and_snapshot(
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
        STATE_PROJECT_ID: resolved_project_id,
        STATE_SNAPSHOT: snapshot,
        STATE_TRACE_ID: trace_id,
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
