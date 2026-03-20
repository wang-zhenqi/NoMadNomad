"""仓储 ``insert`` 用的行字段载荷（Pydantic dataclass；落库前结构化，不等同于领域 ``BaseModel``）。"""

from __future__ import annotations

from pydantic.dataclasses import dataclass


@dataclass
class ProjectInsertPayload:
    """对应 ``projects`` 表一行在插入前的列值。"""

    title: str
    listing_html: str | None = None
    listing_snapshot_json: str | None = None


@dataclass
class AgentRunInsertPayload:
    """对应 ``agent_runs`` 表一行在插入前的列值。"""

    agent_type: str
    success: bool
    project_id: int | None = None
    input_payload_json: str | None = None
    output_payload_json: str | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    trace_id: str | None = None


@dataclass
class AppEventInsertPayload:
    """对应 ``app_events`` 表一行在插入前的列值。"""

    event_type: str
    level: str
    trace_id: str | None = None
    project_id: int | None = None
    source: str | None = None
    payload_json: str | None = None
