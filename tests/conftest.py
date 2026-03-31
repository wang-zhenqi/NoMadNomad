"""pytest 共享 fixture 与配置."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from nomadnomad.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """FastAPI 测试客户端（每个测试一个新 app + 内存 SQLite）。"""
    monkeypatch.setenv("NOMADNOMAD_SQLITE_PATH", ":memory:")
    app = create_app()
    with TestClient(app) as client:
        yield client
