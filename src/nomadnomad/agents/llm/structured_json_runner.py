"""结构化 JSON 调用的通用重试骨架（仅解析失败时重试一次）。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from nomadnomad.agents.llm.json_chat_client import JsonCompletionClient

TParsed = TypeVar("TParsed")


@dataclass(frozen=True)
class StructuredJsonRunResult(Generic[TParsed]):
    parsed: TParsed | None
    last_raw_json: str | None
    error_message: str | None


async def complete_json_then_parse_with_one_repair_retry(
    *,
    llm_client: JsonCompletionClient,
    system_prompt: str,
    base_user_prompt: str,
    repair_suffix: str,
    parse: Callable[[str], TParsed],
    parse_exceptions: tuple[type[Exception], ...],
    on_parse_error: Callable[[int, str, Exception], None],
) -> StructuredJsonRunResult[TParsed]:
    """调用 LLM 并解析结果。

    约束：
    - 仅当 parse 抛出 parse_exceptions 中的异常时重试一次（对 user_prompt 追加 repair_suffix）。
    - LLM 调用异常不重试（调用方负责记录日志）。
    """

    last_raw_json: str | None = None
    for attempt_index in range(2):
        user_prompt = base_user_prompt if attempt_index == 0 else base_user_prompt + repair_suffix
        last_raw_json = await llm_client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        try:
            parsed = parse(last_raw_json)
        except parse_exceptions as exc:
            on_parse_error(attempt_index, last_raw_json, exc)
            if attempt_index == 0:
                continue
            return StructuredJsonRunResult(
                parsed=None,
                last_raw_json=last_raw_json,
                error_message=f"parse_failed: {exc}",
            )
        else:
            return StructuredJsonRunResult(parsed=parsed, last_raw_json=last_raw_json, error_message=None)

    return StructuredJsonRunResult(parsed=None, last_raw_json=last_raw_json, error_message="parse_failed: unknown")
