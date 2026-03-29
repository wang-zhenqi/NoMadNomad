"""Story 4：需求分析单节点 — 快照或规范化文本 → ``RequirementAnalysis``，并写入 ``agent_runs``。"""

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
from nomadnomad.db.repositories import AgentRunRepo
from nomadnomad.models import JobPostingSnapshot, RequirementAnalysis
from nomadnomad.schemas.contract_parse import parse_requirement_analysis

REQUIREMENT_ANALYSIS_AGENT_TYPE = "requirement_analyzer"

REQUIREMENT_ANALYSIS_SYSTEM_PROMPT = """You are an expert at extracting structured job requirements from freelance postings.
Respond with a single JSON object only (no markdown fences). The object must match this shape:
- technology_stack: array of strings (languages, frameworks, tools)
- key_requirements: array of strings (must-have deliverables or constraints)
- budget_summary: string or null
- timeline_summary: string or null
- complexity_notes: string or null
- risk_notes: string or null
- source_job_uid: string or null (copy from input when present)
Use empty arrays where unknown. Use null for unknown scalar fields."""

_USER_PROMPT_REPAIR_SUFFIX = (
    "\n\nYour previous answer could not be parsed for the schema. "
    "Reply with one JSON object only, no code fences, no extra text."
)


@dataclass
class RequirementAnalysisAgentOutcome:
    """单次 Agent 运行结果（成功时 ``analysis`` 非空）。"""

    analysis: RequirementAnalysis | None
    agent_run_id: int
    error_message: str | None


def _validate_exactly_one_input(
    *,
    snapshot: JobPostingSnapshot | None,
    normalized_job_text: str | None,
) -> None:
    has_snapshot = snapshot is not None
    has_text = normalized_job_text is not None
    if has_snapshot == has_text:
        raise ValueError("Provide exactly one of snapshot= or normalized_job_text=")


def _build_user_prompt_from_snapshot(snapshot: JobPostingSnapshot) -> str:
    payload = snapshot.model_dump(mode="json")
    return (
        "You are given a structured JobPostingSnapshot as JSON. "
        "Infer RequirementAnalysis fields from it.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _build_user_prompt_from_normalized_text(normalized_job_text: str) -> str:
    return "You are given job posting text. Infer RequirementAnalysis fields.\n\n" f"{normalized_job_text.strip()}"


def _input_payload_dict(
    *,
    snapshot: JobPostingSnapshot | None,
    normalized_job_text: str | None,
) -> dict[str, Any]:
    if snapshot is not None:
        return {
            "input_kind": "job_posting_snapshot",
            "snapshot": json.loads(snapshot.model_dump_json()),
        }
    assert normalized_job_text is not None
    return {"input_kind": "normalized_text", "normalized_job_text": normalized_job_text}


def _truncate_for_storage(text: str, max_chars: int = 16000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…(truncated)"


async def run_requirement_analysis_agent(
    connection: aiosqlite.Connection,
    *,
    project_id: int,
    llm_client: JsonCompletionClient,
    snapshot: JobPostingSnapshot | None = None,
    normalized_job_text: str | None = None,
    trace_id: str | None = None,
) -> RequirementAnalysisAgentOutcome:
    """调用 LLM 产出 ``RequirementAnalysis``，并写入 ``agent_runs``。

    解析失败时最多再请求一次 LLM（附加修复提示）。其它异常（如 HTTP）不重试。
    """
    _validate_exactly_one_input(snapshot=snapshot, normalized_job_text=normalized_job_text)

    if snapshot is not None:
        base_user_prompt = _build_user_prompt_from_snapshot(snapshot)
    else:
        base_user_prompt = _build_user_prompt_from_normalized_text(normalized_job_text or "")

    input_payload = _input_payload_dict(snapshot=snapshot, normalized_job_text=normalized_job_text)
    input_payload_json = json.dumps(input_payload, ensure_ascii=False)

    started = time.perf_counter()
    last_error: str | None = None
    last_raw_json: str | None = None

    log = logger.bind(
        project_id=project_id,
        agent_type=REQUIREMENT_ANALYSIS_AGENT_TYPE,
        trace_id=trace_id,
    )
    log.info("requirement_analysis_agent_started")

    for attempt_index in range(2):
        user_prompt = base_user_prompt if attempt_index == 0 else base_user_prompt + _USER_PROMPT_REPAIR_SUFFIX
        try:
            last_raw_json = await llm_client.complete_json(
                system_prompt=REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            last_error = f"llm_call_failed: {exc}"
            log.exception("requirement_analysis_llm_call_failed")
            break

        try:
            analysis = parse_requirement_analysis(last_raw_json)
        except (ValueError, ValidationError) as exc:
            last_error = f"parse_failed: {exc}"
            log.warning(
                "requirement_analysis_parse_failed",
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
                    agent_type=REQUIREMENT_ANALYSIS_AGENT_TYPE,
                    input_payload_json=input_payload_json,
                    output_payload_json=analysis.model_dump_json(),
                    success=True,
                    duration_ms=duration_ms,
                    error_message=None,
                    trace_id=trace_id,
                ),
            )
            log.info("requirement_analysis_agent_completed", agent_run_id=agent_run_id, duration_ms=duration_ms)
            return RequirementAnalysisAgentOutcome(
                analysis=analysis,
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
            agent_type=REQUIREMENT_ANALYSIS_AGENT_TYPE,
            input_payload_json=input_payload_json,
            output_payload_json=failure_output,
            success=False,
            duration_ms=duration_ms,
            error_message=last_error,
            trace_id=trace_id,
        ),
    )
    log.warning(
        "requirement_analysis_agent_failed",
        agent_run_id=agent_run_id,
        duration_ms=duration_ms,
        error_message=last_error,
    )
    return RequirementAnalysisAgentOutcome(
        analysis=None,
        agent_run_id=agent_run_id,
        error_message=last_error,
    )
