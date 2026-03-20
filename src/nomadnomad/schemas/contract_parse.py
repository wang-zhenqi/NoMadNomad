"""将 JSON 字符串或 dict 校验为领域 Schema。"""

from __future__ import annotations

import json
from typing import Any

from nomadnomad.models.proposal import Proposal
from nomadnomad.models.requirement_analysis import RequirementAnalysis


def _coerce_mapping(raw: str | dict[str, Any], *, context_label: str) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{context_label}: invalid JSON ({exc.msg})") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{context_label}: JSON root must be an object")
    return parsed


def parse_requirement_analysis(raw: str | dict[str, Any]) -> RequirementAnalysis:
    """校验并构造 ``RequirementAnalysis``。``raw`` 为 JSON 对象字符串或已解析的 dict。"""
    payload = _coerce_mapping(raw, context_label="requirement analysis")
    return RequirementAnalysis.model_validate(payload)


def parse_proposal(raw: str | dict[str, Any]) -> Proposal:
    """校验并构造 ``Proposal``。``raw`` 为 JSON 对象字符串或已解析的 dict。"""
    payload = _coerce_mapping(raw, context_label="proposal")
    return Proposal.model_validate(payload)
