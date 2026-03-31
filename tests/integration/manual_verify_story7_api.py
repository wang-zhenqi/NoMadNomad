"""手动验收脚本：Story 7 业务 API 端到端闭环。

放在 tests/integration/ 下但不以 test_ 开头，避免 pytest 自动收集。

用法示例：

1) 启动 API（建议使用磁盘库便于复查）
   export NOMADNOMAD_SQLITE_PATH="data/nomadnomad.sqlite"
   poetry run init-sqlite-db
   poetry run serve-api

2) 配置真实 LLM（或替换为你自己的 OpenAI 兼容网关）
   export NOMADNOMAD_LLM_API_KEY="..."
   export NOMADNOMAD_LLM_BASE_URL="https://api.openai.com/v1"
   export NOMADNOMAD_LLM_MODEL="gpt-4o-mini"

3) 运行手动验收脚本
   poetry run python tests/integration/manual_verify_story7_api.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


def _demo_html() -> str:
    demo_path = Path(__file__).resolve().parents[3] / "resources" / "demo" / "demo_requirement.html"
    return demo_path.read_text(encoding="utf-8")


def _pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def main() -> None:
    base_url = os.environ.get("NOMADNOMAD_API_BASE_URL", "http://localhost:8000").rstrip("/")

    with httpx.Client(base_url=base_url, timeout=120.0) as client:
        print(f"[1/5] POST /projects  base_url={base_url}")
        create_resp = client.post("/projects", json={"listing_html": _demo_html()})
        print(f"status={create_resp.status_code}")
        create_resp.raise_for_status()
        create_payload = create_resp.json()
        print(_pretty(create_payload))
        project_id = create_payload["project_id"]

        print(f"\n[2/5] POST /projects/{project_id}/analyze")
        analyze_resp = client.post(f"/projects/{project_id}/analyze")
        print(f"status={analyze_resp.status_code}")
        analyze_resp.raise_for_status()
        analyze_payload = analyze_resp.json()
        print(_pretty(analyze_payload))
        requirement_analysis_id = analyze_payload["requirement_analysis_id"]

        print(f"\n[3/5] POST /projects/{project_id}/proposals")
        proposal_resp = client.post(f"/projects/{project_id}/proposals")
        print(f"status={proposal_resp.status_code}")
        proposal_resp.raise_for_status()
        proposal_payload = proposal_resp.json()
        print(_pretty(proposal_payload))
        proposal_id = proposal_payload["proposal_id"]

        print(f"\n[4/5] GET /projects/{project_id}")
        project_resp = client.get(f"/projects/{project_id}")
        print(f"status={project_resp.status_code}")
        project_resp.raise_for_status()
        project_payload = project_resp.json()
        print(_pretty(project_payload))

        print(f"\n[5/5] GET /proposals/{proposal_id}")
        proposal_get = client.get(f"/proposals/{proposal_id}")
        print(f"status={proposal_get.status_code}")
        proposal_get.raise_for_status()
        proposal_get_payload = proposal_get.json()
        print(_pretty(proposal_get_payload))

    print(
        "\nOK. 关键 ID："
        f" project_id={project_id}"
        f" requirement_analysis_id={requirement_analysis_id}"
        f" proposal_id={proposal_id}"
    )


if __name__ == "__main__":
    main()
