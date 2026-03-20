"""CLI：读取 Upwork 职位 HTML，打印 Story 1（快照）+ Story 2（契约校验后）的集成效果。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nomadnomad.ingest import HtmlParseError, parse_upwork_job_html
from nomadnomad.preview import (
    example_proposal_payload_from_snapshot,
    requirement_payload_from_snapshot,
)
from nomadnomad.schemas import parse_proposal, parse_requirement_analysis


def _default_demo_html_path() -> Path:
    """仓库内 golden 样例：`resources/demo/demo_requirement.html`。"""
    return Path(__file__).resolve().parents[3] / "resources" / "demo" / "demo_requirement.html"


def _print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def _print_json(data: object) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    print(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="读取 Upwork 职位 HTML，展示 HTML→快照→需求分析/提案契约的流水线输出。",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="HTML 文件路径；默认使用仓库内 resources/demo/demo_requirement.html",
    )
    args = parser.parse_args(argv)

    html_path = args.html if args.html is not None else _default_demo_html_path()
    if not html_path.is_file():
        print(f"错误：找不到 HTML 文件：{html_path}", file=sys.stderr)
        print("请使用 --html 指定有效路径，或在仓库根目录运行本命令。", file=sys.stderr)
        return 1

    raw_html = html_path.read_text(encoding="utf-8")
    try:
        snapshot = parse_upwork_job_html(raw_html)
    except HtmlParseError as exc:
        print(f"解析失败：{exc}", file=sys.stderr)
        return 2

    _print_section("Story 1 — JobPostingSnapshot（Pydantic → JSON）")
    _print_json(snapshot.model_dump())

    requirement_payload = requirement_payload_from_snapshot(snapshot)
    analysis = parse_requirement_analysis(requirement_payload)

    _print_section("Story 2 — 需求分析：raw payload（由快照推导的 dict）")
    _print_json(requirement_payload)
    _print_section("Story 2 — 需求分析：parse_requirement_analysis 校验后")
    _print_json(analysis.model_dump())

    proposal_payload = example_proposal_payload_from_snapshot(snapshot)
    proposal = parse_proposal(proposal_payload)

    _print_section("Story 2 — 提案：raw payload（示例）")
    _print_json(proposal_payload)
    _print_section("Story 2 — 提案：parse_proposal 校验后（JSON）；正文为 Markdown")
    _print_json(proposal.model_dump())

    print()
    print(f"来源文件：{html_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
