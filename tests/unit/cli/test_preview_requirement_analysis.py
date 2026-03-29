"""CLI：preview-requirement-analysis."""

from __future__ import annotations

from pathlib import Path

import pytest

from nomadnomad.cli.preview_requirement_analysis import main

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_preview_requirement_analysis_mock_llm_prints_analysis(capsys) -> None:
    """离线 --mock-llm：走 Agent + agent_runs，输出含职位 uid 与分析字段。"""
    demo = REPO_ROOT / "resources" / "demo" / "demo_requirement.html"
    exit_code = main(["--html", str(demo), "--mock-llm"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "2034153922546495276" in out
    assert "RequirementAnalysis" in out or "technology_stack" in out
    assert "agent_run_id" in out.lower() or "agent_run" in out.lower()


def test_preview_requirement_analysis_missing_file_returns_one() -> None:
    assert main(["--html", "/nonexistent/nomadnomad_missing.html", "--mock-llm"]) == 1


def test_preview_requirement_analysis_real_mode_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """未设置 API Key 且非 mock：Agent 失败，退出码非 0。"""
    monkeypatch.setenv("NOMADNOMAD_LLM_API_KEY", "")
    demo = REPO_ROOT / "resources" / "demo" / "demo_requirement.html"
    exit_code = main(["--html", str(demo)])
    assert exit_code != 0
