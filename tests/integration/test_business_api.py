"""Story 7：业务 API 集成测试（创建项目 → 分析 → 生成提案 → 查询）。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from nomadnomad.agents.llm.json_chat_client import JsonCompletionClient
from nomadnomad.api.dependencies import get_llm_client
from nomadnomad.main import create_app
from nomadnomad.preview import RecordingSequentialJsonClient


def _demo_html() -> str:
    demo_path = Path(__file__).resolve().parents[2] / "resources" / "demo" / "demo_requirement.html"
    return demo_path.read_text(encoding="utf-8")


VALID_ANALYSIS_JSON = json.dumps(
    {
        "technology_stack": ["Python"],
        "key_requirements": ["Low latency"],
        "budget_summary": "$10–$40 hourly",
        "timeline_summary": "1–3 months",
        "complexity_notes": None,
        "risk_notes": None,
        "source_job_uid": "2034153922546495276",
    },
    ensure_ascii=False,
)

VALID_PROPOSAL_JSON = json.dumps(
    {
        "title": "Experienced Python automation",
        "body_markdown": "## Approach\n\nI will use **Python**.\n\nThanks.",
        "template_variables": {"client_name": "there"},
    },
    ensure_ascii=False,
)


def _create_test_app(*, llm_client: JsonCompletionClient):
    app = create_app()
    app.dependency_overrides[get_llm_client] = lambda: llm_client
    return app


def test_story7_end_to_end_create_analyze_generate_and_query(monkeypatch) -> None:
    """S7-06：端到端闭环（创建项目→分析→生成提案→查询）。"""
    monkeypatch.setenv("NOMADNOMAD_SQLITE_PATH", ":memory:")
    fake_llm = RecordingSequentialJsonClient([VALID_ANALYSIS_JSON, VALID_PROPOSAL_JSON])
    app = _create_test_app(llm_client=fake_llm)

    with TestClient(app) as client:
        create_resp = client.post("/projects", json={"listing_html": _demo_html()})
        assert create_resp.status_code == 200
        project_id = create_resp.json()["project_id"]

        analyze_resp = client.post(f"/projects/{project_id}/analyze")
        assert analyze_resp.status_code == 200
        analysis_id = analyze_resp.json()["requirement_analysis_id"]
        assert isinstance(analysis_id, int)

        proposal_resp = client.post(f"/projects/{project_id}/proposals")
        assert proposal_resp.status_code == 200
        proposal_id = proposal_resp.json()["proposal_id"]
        assert isinstance(proposal_id, int)

        project_resp = client.get(f"/projects/{project_id}")
        assert project_resp.status_code == 200
        payload = project_resp.json()
        assert payload["id"] == project_id
        assert payload["latest_requirement_analysis_id"] == analysis_id
        assert payload["latest_proposal_id"] == proposal_id

        proposal_get = client.get(f"/proposals/{proposal_id}")
        assert proposal_get.status_code == 200
        assert "body_markdown" in proposal_get.json()
