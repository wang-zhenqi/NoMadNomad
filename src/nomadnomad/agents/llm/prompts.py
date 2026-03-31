"""LLM 交互中复用的 Prompt 片段。"""

from __future__ import annotations

JSON_REPAIR_SUFFIX = (
    "\n\nYour previous answer could not be parsed for the schema. "
    "Reply with one JSON object only, no code fences, no extra text."
)
