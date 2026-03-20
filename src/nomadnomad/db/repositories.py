"""按表划分的薄仓储：插入与按主键查询。"""

from __future__ import annotations

from typing import Any

import aiosqlite

from nomadnomad.db.insert_payloads import AgentRunInsertPayload, AppEventInsertPayload, ProjectInsertPayload
from nomadnomad.models import Proposal, RequirementAnalysis


async def _execute_insert_and_commit_return_row_id(
    connection: aiosqlite.Connection,
    *,
    sql: str,
    parameters: tuple[Any, ...],
    table_label: str,
) -> int:
    """执行 INSERT、提交，并返回 ``lastrowid``（缺失时抛错，消息与旧实现一致）。"""
    cursor = await connection.execute(sql, parameters)
    await connection.commit()
    row_id = cursor.lastrowid
    if row_id is None:
        raise RuntimeError(f"INSERT {table_label} did not produce lastrowid")
    return int(row_id)


async def _fetch_optional_row_dict(
    connection: aiosqlite.Connection,
    *,
    sql: str,
    parameters: tuple[Any, ...],
) -> dict[str, Any] | None:
    """执行单行查询；无行返回 ``None``，否则 ``dict(row)``。"""
    cursor = await connection.execute(sql, parameters)
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


class ProjectRepo:
    @staticmethod
    async def insert(connection: aiosqlite.Connection, row_to_insert: ProjectInsertPayload) -> int:
        return await _execute_insert_and_commit_return_row_id(
            connection,
            sql="""
            INSERT INTO projects (title, listing_html, listing_snapshot_json)
            VALUES (?, ?, ?)
            """,
            parameters=(
                row_to_insert.title,
                row_to_insert.listing_html,
                row_to_insert.listing_snapshot_json,
            ),
            table_label="projects",
        )

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        project_id: int,
    ) -> dict[str, Any] | None:
        return await _fetch_optional_row_dict(
            connection,
            sql="SELECT id, title, listing_html, listing_snapshot_json, created_at FROM projects WHERE id = ?",
            parameters=(project_id,),
        )


class RequirementAnalysisRepo:
    @staticmethod
    async def insert(
        connection: aiosqlite.Connection,
        *,
        project_id: int,
        analysis: RequirementAnalysis,
    ) -> int:
        analysis_json = analysis.model_dump_json()
        return await _execute_insert_and_commit_return_row_id(
            connection,
            sql="""
            INSERT INTO requirement_analyses (project_id, analysis_json)
            VALUES (?, ?)
            """,
            parameters=(project_id, analysis_json),
            table_label="requirement_analyses",
        )

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        analysis_id: int,
    ) -> dict[str, Any] | None:
        return await _fetch_optional_row_dict(
            connection,
            sql="SELECT id, project_id, analysis_json, created_at FROM requirement_analyses WHERE id = ?",
            parameters=(analysis_id,),
        )


class ProposalRepo:
    @staticmethod
    async def insert(
        connection: aiosqlite.Connection,
        *,
        project_id: int,
        proposal: Proposal,
    ) -> int:
        proposal_json = proposal.model_dump_json()
        return await _execute_insert_and_commit_return_row_id(
            connection,
            sql="""
            INSERT INTO proposals (project_id, proposal_json)
            VALUES (?, ?)
            """,
            parameters=(project_id, proposal_json),
            table_label="proposals",
        )

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        proposal_id: int,
    ) -> dict[str, Any] | None:
        return await _fetch_optional_row_dict(
            connection,
            sql="SELECT id, project_id, proposal_json, created_at FROM proposals WHERE id = ?",
            parameters=(proposal_id,),
        )


class AgentRunRepo:
    @staticmethod
    async def insert(connection: aiosqlite.Connection, row_to_insert: AgentRunInsertPayload) -> int:
        success_int = 1 if row_to_insert.success else 0
        return await _execute_insert_and_commit_return_row_id(
            connection,
            sql="""
            INSERT INTO agent_runs (
                project_id, agent_type, input_payload_json, output_payload_json,
                success, duration_ms, error_message, trace_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            parameters=(
                row_to_insert.project_id,
                row_to_insert.agent_type,
                row_to_insert.input_payload_json,
                row_to_insert.output_payload_json,
                success_int,
                row_to_insert.duration_ms,
                row_to_insert.error_message,
                row_to_insert.trace_id,
            ),
            table_label="agent_runs",
        )

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        agent_run_id: int,
    ) -> dict[str, Any] | None:
        return await _fetch_optional_row_dict(
            connection,
            sql="""
            SELECT id, project_id, agent_type, input_payload_json, output_payload_json,
                   success, duration_ms, error_message, trace_id, created_at
            FROM agent_runs WHERE id = ?
            """,
            parameters=(agent_run_id,),
        )


class AppEventRepo:
    @staticmethod
    async def insert(connection: aiosqlite.Connection, row_to_insert: AppEventInsertPayload) -> int:
        return await _execute_insert_and_commit_return_row_id(
            connection,
            sql="""
            INSERT INTO app_events (event_type, level, trace_id, project_id, source, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            parameters=(
                row_to_insert.event_type,
                row_to_insert.level,
                row_to_insert.trace_id,
                row_to_insert.project_id,
                row_to_insert.source,
                row_to_insert.payload_json,
            ),
            table_label="app_events",
        )

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        event_id: int,
    ) -> dict[str, Any] | None:
        return await _fetch_optional_row_dict(
            connection,
            sql="""
            SELECT id, event_type, level, trace_id, project_id, source, payload_json, created_at
            FROM app_events WHERE id = ?
            """,
            parameters=(event_id,),
        )
