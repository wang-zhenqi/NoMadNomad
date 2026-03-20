"""CLI：preview-job-html."""

from __future__ import annotations

from pathlib import Path

from nomadnomad.cli.preview_job_html import main

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_preview_job_html_prints_pipeline_sections(capsys) -> None:
    demo = REPO_ROOT / "resources" / "demo" / "demo_requirement.html"
    exit_code = main(["--html", str(demo)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Story 1" in out
    assert "Story 2" in out
    assert "2034153922546495276" in out


def test_preview_job_html_missing_file_returns_one() -> None:
    assert main(["--html", "/nonexistent/nomadnomad_missing.html"]) == 1
