"""OpenAI 兼容：JSON 模式聊天补全（httpx）。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx
from loguru import logger

from nomadnomad.config.llm_settings import LlmSettings


@runtime_checkable
class JsonCompletionClient(Protocol):
    """可替换的 LLM 客户端（测试注入 mock）。"""

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        """返回模型输出的 JSON 字符串（不含 markdown 围栏）。"""
        ...


class OpenAiCompatibleJsonChatClient:
    """通过 ``/chat/completions`` + ``response_format=json_object`` 请求结构化 JSON。"""

    def __init__(
        self,
        settings: LlmSettings,
        *,
        request_timeout_seconds: float = 120.0,
    ) -> None:
        self._settings = settings
        self._request_timeout_seconds = request_timeout_seconds

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        api_key = self._settings.llm_api_key
        if not api_key:
            raise RuntimeError("NOMADNOMAD_LLM_API_KEY is not set; cannot call the LLM")

        url = f"{self._settings.llm_base_url.rstrip('/')}/chat/completions"
        payload: dict[str, object] = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self._request_timeout_seconds) as http_client:
                response = await http_client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.bind(url=url).exception("llm_http_request_failed")
            raise RuntimeError(f"LLM HTTP request failed: {exc}") from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.bind(response_keys=list(data) if isinstance(data, dict) else type(data)).exception(
                "llm_response_shape_unexpected"
            )
            raise RuntimeError("LLM response JSON missing choices[0].message.content") from exc

        if not isinstance(content, str):
            raise RuntimeError("LLM message content is not a string")
        return content
