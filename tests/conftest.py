"""pytest 共享 fixture 与配置."""

import pytest
from fastapi.testclient import TestClient

from nomadnomad.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI 测试客户端."""
    return TestClient(app)
