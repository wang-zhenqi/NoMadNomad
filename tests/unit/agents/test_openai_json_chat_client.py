"""OpenAI 兼容 JSON 聊天客户端（mock httpx）。"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from nomadnomad.agents.llm.json_chat_client import OpenAiCompatibleJsonChatClient
from nomadnomad.config.llm_settings import LlmSettings


@pytest.mark.asyncio
async def test_openai_compatible_json_chat_client_returns_message_content() -> None:
    """S4-04：HTTP 200 + 标准 choices 形状 → 返回 message.content 字符串。"""
    expected_json = json.dumps({"technology_stack": ["Go"], "key_requirements": []})
    request = httpx.Request("POST", "https://example.test/v1/chat/completions")
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": expected_json}}]},
        request=request,
    )
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.post = AsyncMock(return_value=mock_response)

    settings = LlmSettings(llm_base_url="https://example.test/v1", llm_model="test-model", llm_api_key="sk-test")

    with patch("nomadnomad.agents.llm.json_chat_client.httpx.AsyncClient", return_value=mock_client_instance):
        client = OpenAiCompatibleJsonChatClient(settings)
        out = await client.complete_json(system_prompt="sys", user_prompt="usr")

    assert out == expected_json
    mock_client_instance.post.assert_called_once()
    posted_url = mock_client_instance.post.call_args[0][0]
    assert str(posted_url).endswith("/chat/completions")


@pytest.mark.asyncio
async def test_openai_compatible_json_chat_client_missing_api_key_raises() -> None:
    """未配置 API Key 时给出明确错误。"""
    settings = LlmSettings(llm_api_key=None)
    client = OpenAiCompatibleJsonChatClient(settings)
    with pytest.raises(RuntimeError, match="NOMADNOMAD_LLM_API_KEY"):
        await client.complete_json(system_prompt="s", user_prompt="u")
