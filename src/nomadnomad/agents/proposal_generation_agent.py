"""Story 5：提案生成单节点 — ``RequirementAnalysis`` → ``Proposal``，并写入 ``agent_runs``。"""

from __future__ import annotations

import json
import time
from typing import Any

import aiosqlite
from loguru import logger
from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from nomadnomad.agents.llm.json_chat_client import JsonCompletionClient
from nomadnomad.db.insert_payloads import AgentRunInsertPayload
from nomadnomad.db.repositories import AgentRunRepo, RequirementAnalysisRepo
from nomadnomad.models import Proposal, RequirementAnalysis
from nomadnomad.schemas.contract_parse import parse_proposal, parse_requirement_analysis

PROPOSAL_GENERATION_AGENT_TYPE = "proposal_generator"

PROPOSAL_MAX_BODY_MARKDOWN_CHARS = 80_000

PROPOSAL_SYSTEM_PROMPT = """You are an expert freelance proposal writer.
Respond with a single JSON object only (no markdown fences). The object must match this shape:
- title: string (short cover line for the proposal)
- body_markdown: string (the full proposal in Markdown: headings, bullets, emphasis as appropriate)
- template_variables: object mapping string keys to string values (optional placeholders; use {} if none)
The proposal should address the requirement analysis: tech stack, deliverables, timeline/budget context.
Use professional, concise language."""

_USER_PROMPT_REPAIR_SUFFIX = (
    "\n\nYour previous answer could not be parsed for the schema. "
    "Reply with one JSON object only, no code fences, no extra text."
)


@dataclass
class ProposalGenerationAgentOutcome:
    """单次 Agent 运行结果（成功时 ``proposal`` 非空）。"""

    proposal: Proposal | None
    agent_run_id: int
    error_message: str | None


def _validate_exactly_one_analysis_input(
    *,
    requirement_analysis: RequirementAnalysis | None,
    requirement_analysis_id: int | None,
) -> None:
    has_obj = requirement_analysis is not None
    has_id = requirement_analysis_id is not None
    if has_obj == has_id:
        raise ValueError("Provide exactly one of requirement_analysis= or requirement_analysis_id=")


def _build_user_prompt_from_analysis(analysis: RequirementAnalysis) -> str:
    payload = analysis.model_dump(mode="json")
    return (
        "You are given a structured RequirementAnalysis as JSON. "
        "Write a compelling Upwork proposal as specified in the system prompt.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _input_payload_dict(
    *,
    analysis: RequirementAnalysis,
    requirement_analysis_id: int | None,
) -> dict[str, Any]:
    return {
        "input_kind": "requirement_analysis",
        "requirement_analysis": json.loads(analysis.model_dump_json()),
        "requirement_analysis_id": requirement_analysis_id,
    }


def _truncate_for_storage(text: str, max_chars: int = 16000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…(truncated)"


def _validate_proposal_reasonable(proposal: Proposal) -> None:
    if len(proposal.body_markdown) > PROPOSAL_MAX_BODY_MARKDOWN_CHARS:
        raise ValueError(f"proposal body_markdown exceeds max length ({PROPOSAL_MAX_BODY_MARKDOWN_CHARS} characters)")


async def _resolve_requirement_analysis(
    connection: aiosqlite.Connection,
    *,
    requirement_analysis: RequirementAnalysis | None,
    requirement_analysis_id: int | None,
) -> tuple[RequirementAnalysis, int | None]:
    if requirement_analysis is not None:
        return requirement_analysis, None
    assert requirement_analysis_id is not None
    row = await RequirementAnalysisRepo.get_by_id(connection, requirement_analysis_id)
    if row is None:
        raise ValueError(f"requirement_analysis_id={requirement_analysis_id} not found")
    parsed = parse_requirement_analysis(row["analysis_json"])
    return parsed, requirement_analysis_id


async def run_proposal_generation_agent(
    connection: aiosqlite.Connection,
    *,
    project_id: int,
    llm_client: JsonCompletionClient,
    requirement_analysis: RequirementAnalysis | None = None,
    requirement_analysis_id: int | None = None,
    trace_id: str | None = None,
) -> ProposalGenerationAgentOutcome:
    """调用 LLM 产出 ``Proposal``，并写入 ``agent_runs``。

    解析或合理性校验失败时最多再请求一次 LLM（附加修复提示）。其它异常（如 HTTP）不重试。
    """
    _validate_exactly_one_analysis_input(
        requirement_analysis=requirement_analysis,
        requirement_analysis_id=requirement_analysis_id,
    )

    resolved_analysis, resolved_id = await _resolve_requirement_analysis(
        connection,
        requirement_analysis=requirement_analysis,
        requirement_analysis_id=requirement_analysis_id,
    )

    base_user_prompt = _build_user_prompt_from_analysis(resolved_analysis)
    input_payload = _input_payload_dict(
        analysis=resolved_analysis,
        requirement_analysis_id=resolved_id,
    )
    input_payload_json = json.dumps(input_payload, ensure_ascii=False)

    started = time.perf_counter()
    last_error: str | None = None
    last_raw_json: str | None = None

    log = logger.bind(
        project_id=project_id,
        agent_type=PROPOSAL_GENERATION_AGENT_TYPE,
        trace_id=trace_id,
    )
    log.info("proposal_generation_agent_started")

    for attempt_index in range(2):
        user_prompt = base_user_prompt if attempt_index == 0 else base_user_prompt + _USER_PROMPT_REPAIR_SUFFIX
        try:
            last_raw_json = await llm_client.complete_json(
                system_prompt=PROPOSAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            last_error = f"llm_call_failed: {exc}"
            log.exception("proposal_generation_llm_call_failed")
            break

        try:
            proposal = parse_proposal(last_raw_json)
            _validate_proposal_reasonable(proposal)
        except (ValueError, ValidationError) as exc:
            last_error = f"parse_failed: {exc}"
            log.warning(
                "proposal_generation_parse_failed",
                attempt=attempt_index,
                raw_excerpt=_truncate_for_storage(last_raw_json, 400),
            )
            if attempt_index == 0:
                continue
            break
        else:
            duration_ms = int((time.perf_counter() - started) * 1000)
            agent_run_id = await AgentRunRepo.insert(
                connection,
                row_to_insert=AgentRunInsertPayload(
                    project_id=project_id,
                    agent_type=PROPOSAL_GENERATION_AGENT_TYPE,
                    input_payload_json=input_payload_json,
                    output_payload_json=proposal.model_dump_json(),
                    success=True,
                    duration_ms=duration_ms,
                    error_message=None,
                    trace_id=trace_id,
                ),
            )
            log.info("proposal_generation_agent_completed", agent_run_id=agent_run_id, duration_ms=duration_ms)
            return ProposalGenerationAgentOutcome(
                proposal=proposal,
                agent_run_id=agent_run_id,
                error_message=None,
            )

    duration_ms = int((time.perf_counter() - started) * 1000)
    failure_output: str | None = None
    if last_raw_json is not None:
        failure_output = json.dumps({"llm_response_excerpt": _truncate_for_storage(last_raw_json)}, ensure_ascii=False)

    agent_run_id = await AgentRunRepo.insert(
        connection,
        row_to_insert=AgentRunInsertPayload(
            project_id=project_id,
            agent_type=PROPOSAL_GENERATION_AGENT_TYPE,
            input_payload_json=input_payload_json,
            output_payload_json=failure_output,
            success=False,
            duration_ms=duration_ms,
            error_message=last_error,
            trace_id=trace_id,
        ),
    )
    log.warning(
        "proposal_generation_agent_failed",
        agent_run_id=agent_run_id,
        duration_ms=duration_ms,
        error_message=last_error,
    )
    return ProposalGenerationAgentOutcome(
        proposal=None,
        agent_run_id=agent_run_id,
        error_message=last_error,
    )
