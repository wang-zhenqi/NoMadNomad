"""离线/测试用的 fake LLM JSON 客户端（实现 JsonCompletionClient 协议）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FixedJsonClient:
    """总是返回固定 JSON 字符串。"""

    json_body: str

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        return self.json_body


@dataclass
class SequentialJsonClient:
    """按调用顺序依次返回预设 JSON 字符串。"""

    response_bodies: list[str]
    call_index: int = 0

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        body = self.response_bodies[self.call_index]
        self.call_index += 1
        return body


@dataclass
class RecordingSequentialJsonClient(SequentialJsonClient):
    """顺序返回 + 记录 system/user prompt，便于断言调用行为。"""

    system_prompts: list[str] = field(default_factory=list)
    user_prompts: list[str] = field(default_factory=list)

    async def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        self.system_prompts.append(system_prompt)
        self.user_prompts.append(user_prompt)
        return await super().complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
