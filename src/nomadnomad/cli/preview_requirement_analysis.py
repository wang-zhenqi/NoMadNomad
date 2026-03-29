"""CLI：HTML → JobPostingSnapshot → Story 4 需求分析 Agent（真实 LLM 或 ``--mock-llm``）。"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from nomadnomad.agents.llm.json_chat_client import JsonCompletionClient, OpenAiCompatibleJsonChatClient
from nomadnomad.agents.requirement_analysis_agent import run_requirement_analysis_agent
from nomadnomad.config.llm_settings import LlmSettings
from nomadnomad.db import ProjectInsertPayload, ProjectRepo, connect_memory, init_schema
from nomadnomad.ingest import HtmlParseError, parse_upwork_job_html
from nomadnomad.preview import requirement_payload_from_snapshot


def _default_demo_html_path() -> Path:
    """仓库内 golden 样例：``resources/demo/demo_requirement.html``。"""
    return Path(__file__).resolve().parents[3] / "resources" / "demo" / "demo_requirement.html"


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_json(data: object) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    print(text)


class _MockLlmJsonClient:
    """用快照推导的契约 JSON 模拟 LLM，便于离线预览。"""

    def __init__(self, json_body: str) -> None:
        self._json_body = json_body

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        return self._json_body


async def _async_main(*, html_path: Path, use_mock_llm: bool) -> int:
    raw_html = html_path.read_text(encoding="utf-8")
    try:
        snapshot = parse_upwork_job_html(raw_html)
    except HtmlParseError as exc:
        print(f"解析失败：{exc}", file=sys.stderr)
        return 2

    if use_mock_llm:
        mock_payload = requirement_payload_from_snapshot(snapshot)
        mock_json = json.dumps(mock_payload, ensure_ascii=False)
        llm_client: JsonCompletionClient = _MockLlmJsonClient(mock_json)
    else:
        llm_client = OpenAiCompatibleJsonChatClient(LlmSettings())

    async with connect_memory() as connection:
        await init_schema(connection)
        project_id = await ProjectRepo.insert(
            connection,
            row_to_insert=ProjectInsertPayload(
                title=snapshot.title or "preview-job",
                listing_html=None,
                listing_snapshot_json=snapshot.model_dump_json(),
            ),
        )
        outcome = await run_requirement_analysis_agent(
            connection,
            project_id=project_id,
            snapshot=snapshot,
            llm_client=llm_client,
            trace_id="preview-requirement-analysis-cli",
        )

    if outcome.analysis is None:
        print(f"需求分析失败：{outcome.error_message}", file=sys.stderr)
        print(f"agent_run_id={outcome.agent_run_id}", file=sys.stderr)
        return 3

    _print_section("Story 4 — RequirementAnalysis（Agent 输出）")
    _print_json(outcome.analysis.model_dump())

    _print_section("Story 4 — agent_run 摘要")
    _print_json(
        {
            "agent_run_id": outcome.agent_run_id,
            "trace_id": "preview-requirement-analysis-cli",
            "mode": "mock_llm" if use_mock_llm else "live_llm",
        }
    )

    print()
    print(f"来源 HTML：{html_path.resolve()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="读取 Upwork 职位 HTML，经 Story 1 解析后调用需求分析 Agent（Story 4），打印结构化结果。",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="HTML 文件路径；默认使用仓库内 resources/demo/demo_requirement.html",
    )
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="不调用真实 LLM：用快照推导的 JSON 模拟模型输出（离线/CI 友好）",
    )
    args = parser.parse_args(argv)

    html_path = args.html if args.html is not None else _default_demo_html_path()
    if not html_path.is_file():
        print(f"错误：找不到 HTML 文件：{html_path}", file=sys.stderr)
        print("请使用 --html 指定有效路径，或在仓库根目录运行本命令。", file=sys.stderr)
        return 1

    return asyncio.run(_async_main(html_path=html_path, use_mock_llm=args.mock_llm))


if __name__ == "__main__":
    raise SystemExit(main())
