"""演示用：从 JobPostingSnapshot 推导 Story 2 的 dict 载荷（非 LLM，仅供预览与测试）。"""

from __future__ import annotations

from typing import Any

from nomadnomad.models import JobPostingSnapshot


def requirement_payload_from_snapshot(snapshot: JobPostingSnapshot) -> dict[str, Any]:
    """用快照字段构造与 `RequirementAnalysis` 兼容的 dict（模拟 Agent 结构化输出）。"""
    budget_summary: str | None = None
    if snapshot.budget is not None and snapshot.budget.min_usd is not None:
        max_part = snapshot.budget.max_usd
        basis = snapshot.budget.basis or "hourly"
        budget_summary = f"${snapshot.budget.min_usd:g}–${max_part:g} {basis}"

    timeline_summary: str | None = None
    if snapshot.engagement is not None:
        timeline_parts = [
            snapshot.engagement.duration_text,
            snapshot.engagement.hours_per_week_text,
        ]
        timeline_summary = " · ".join(part for part in timeline_parts if part)

    complexity_notes = snapshot.engagement.experience_level_text if snapshot.engagement is not None else None

    risk_notes: str | None = None
    if snapshot.activity is not None and snapshot.activity.proposals_text:
        risk_notes = f"Competition: {snapshot.activity.proposals_text} proposals"

    key_requirements: list[str] = []
    summary = snapshot.summary_text or ""
    if "Python-based system" in summary:
        key_requirements.append("Deliver a Python-based image solving system")
    lowered = summary.lower()
    if "within 5s" in lowered or "5 seconds" in lowered:
        key_requirements.append("Meet strict latency target (e.g. within ~5s)")

    return {
        "technology_stack": list(snapshot.mandatory_skills),
        "key_requirements": key_requirements,
        "budget_summary": budget_summary,
        "timeline_summary": timeline_summary,
        "complexity_notes": complexity_notes,
        "risk_notes": risk_notes,
        "source_job_uid": snapshot.job_uid,
    }


def example_proposal_payload_from_snapshot(snapshot: JobPostingSnapshot) -> dict[str, Any]:
    """构造与 `Proposal` 兼容的示例 dict（标题/正文引用快照，便于肉眼验收）。"""
    return {
        "title": f"Proposal aligned with job {snapshot.job_uid}",
        "body_markdown": (
            f"## Fit for **{snapshot.title}**\n\n"
            f"- Stack: {', '.join(snapshot.mandatory_skills)}\n"
            f"- Summary cue: Python-based automation with latency constraints.\n"
        ),
        "template_variables": {"source_job_uid": snapshot.job_uid or ""},
    }
