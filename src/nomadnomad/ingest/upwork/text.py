"""纯文本规范化（与 DOM 无关）。"""

from __future__ import annotations


def normalize_ws(text: str) -> str:
    return " ".join(text.split())
