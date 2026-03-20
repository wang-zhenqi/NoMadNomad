"""按表划分的薄仓储：插入与按主键查询。"""

from __future__ import annotations

from typing import Any

import aiosqlite

from nomadnomad.models import Proposal, RequirementAnalysis


class ProjectRepo:
    @staticmethod
    async def insert(
        connection: aiosqlite.Connection,
        *,
        title: str,
        listing_html: str | None,
        listing_snapshot_json: str | None,
    ) -> int:
        cursor = await connection.execute(
            """
            INSERT INTO projects (title, listing_html, listing_snapshot_json)
            VALUES (?, ?, ?)
            """,
            (title, listing_html, listing_snapshot_json),
        )
        await connection.commit()
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("INSERT projects did not produce lastrowid")
        return int(row_id)

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        project_id: int,
    ) -> dict[str, Any] | None:
        cursor = await connection.execute(
            "SELECT id, title, listing_html, listing_snapshot_json, created_at FROM projects WHERE id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


class RequirementAnalysisRepo:
    @staticmethod
    async def insert(
        connection: aiosqlite.Connection,
        *,
        project_id: int,
        analysis: RequirementAnalysis,
    ) -> int:
        analysis_json = analysis.model_dump_json()
        cursor = await connection.execute(
            """
            INSERT INTO requirement_analyses (project_id, analysis_json)
            VALUES (?, ?)
            """,
            (project_id, analysis_json),
        )
        await connection.commit()
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("INSERT requirement_analyses did not produce lastrowid")
        return int(row_id)

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        analysis_id: int,
    ) -> dict[str, Any] | None:
        cursor = await connection.execute(
            "SELECT id, project_id, analysis_json, created_at FROM requirement_analyses WHERE id = ?",
            (analysis_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


class ProposalRepo:
    @staticmethod
    async def insert(
        connection: aiosqlite.Connection,
        *,
        project_id: int,
        proposal: Proposal,
    ) -> int:
        proposal_json = proposal.model_dump_json()
        cursor = await connection.execute(
            """
            INSERT INTO proposals (project_id, proposal_json)
            VALUES (?, ?)
            """,
            (project_id, proposal_json),
        )
        await connection.commit()
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("INSERT proposals did not produce lastrowid")
        return int(row_id)

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        proposal_id: int,
    ) -> dict[str, Any] | None:
        cursor = await connection.execute(
            "SELECT id, project_id, proposal_json, created_at FROM proposals WHERE id = ?",
            (proposal_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


class AgentRunRepo:
    @staticmethod
    async def insert(
        connection: aiosqlite.Connection,
        *,
        project_id: int | None,
        agent_type: str,
        input_payload_json: str | None,
        output_payload_json: str | None,
        success: bool,
        duration_ms: int | None,
        error_message: str | None,
        trace_id: str | None,
    ) -> int:
        success_int = 1 if success else 0
        cursor = await connection.execute(
            """
            INSERT INTO agent_runs (
                project_id, agent_type, input_payload_json, output_payload_json,
                success, duration_ms, error_message, trace_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                agent_type,
                input_payload_json,
                output_payload_json,
                success_int,
                duration_ms,
                error_message,
                trace_id,
            ),
        )
        await connection.commit()
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("INSERT agent_runs did not produce lastrowid")
        return int(row_id)

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        agent_run_id: int,
    ) -> dict[str, Any] | None:
        cursor = await connection.execute(
            """
            SELECT id, project_id, agent_type, input_payload_json, output_payload_json,
                   success, duration_ms, error_message, trace_id, created_at
            FROM agent_runs WHERE id = ?
            """,
            (agent_run_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


class AppEventRepo:
    @staticmethod
    async def insert(
        connection: aiosqlite.Connection,
        *,
        event_type: str,
        level: str,
        trace_id: str | None,
        project_id: int | None,
        source: str | None,
        payload_json: str | None,
    ) -> int:
        cursor = await connection.execute(
            """
            INSERT INTO app_events (event_type, level, trace_id, project_id, source, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_type, level, trace_id, project_id, source, payload_json),
        )
        await connection.commit()
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("INSERT app_events did not produce lastrowid")
        return int(row_id)

    @staticmethod
    async def get_by_id(
        connection: aiosqlite.Connection,
        event_id: int,
    ) -> dict[str, Any] | None:
        cursor = await connection.execute(
            """
            SELECT id, event_type, level, trace_id, project_id, source, payload_json, created_at
            FROM app_events WHERE id = ?
            """,
            (event_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
