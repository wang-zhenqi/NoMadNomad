"""Agent 内部通用文本处理。"""

from __future__ import annotations


def truncate_for_storage(text: str, max_chars: int = 16000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…(truncated)"
