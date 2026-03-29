"""CLI：preview-proposal-generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from nomadnomad.cli.preview_proposal_generation import main

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_preview_proposal_generation_mock_llm_prints_pipeline(capsys) -> None:
    """离线 --mock-llm：需求分析 + 提案 Agent，输出含 job uid、两类 agent_run。"""
    demo = REPO_ROOT / "resources" / "demo" / "demo_requirement.html"
    exit_code = main(["--html", str(demo), "--mock-llm"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "2034153922546495276" in out
    assert "body_markdown" in out
    assert "requirement_analysis_agent_run_id" in out
    assert "proposal_generation_agent_run_id" in out


def test_preview_proposal_generation_missing_file_returns_one() -> None:
    assert main(["--html", "/nonexistent/nomadnomad_missing.html", "--mock-llm"]) == 1


def test_preview_proposal_generation_real_mode_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """未设置 API Key 且非 mock：第一步 Agent 即失败，退出码非 0。"""
    monkeypatch.setenv("NOMADNOMAD_LLM_API_KEY", "")
    demo = REPO_ROOT / "resources" / "demo" / "demo_requirement.html"
    exit_code = main(["--html", str(demo)])
    assert exit_code != 0
