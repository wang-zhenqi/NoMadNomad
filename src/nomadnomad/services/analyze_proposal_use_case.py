"""Story 6 用例层：解析/加载快照并创建或复用 project。"""

from __future__ import annotations

import aiosqlite

from nomadnomad.db.insert_payloads import ProjectInsertPayload
from nomadnomad.db.repositories import ProjectRepo, ProposalRepo, RequirementAnalysisRepo
from nomadnomad.ingest import parse_upwork_job_html
from nomadnomad.models import JobPostingSnapshot, Proposal, RequirementAnalysis


def validate_exactly_one_job_source(
    *,
    listing_html: str | None,
    job_posting_snapshot: JobPostingSnapshot | None,
    project_id: int | None,
) -> None:
    provided = sum(1 for candidate in (listing_html, job_posting_snapshot, project_id) if candidate is not None)
    if provided != 1:
        raise ValueError("Provide exactly one of listing_html=, job_posting_snapshot=, or project_id=")


async def insert_project_for_snapshot(
    connection: aiosqlite.Connection,
    *,
    snapshot: JobPostingSnapshot,
    listing_html: str | None,
) -> int:
    return await ProjectRepo.insert(
        connection,
        row_to_insert=ProjectInsertPayload(
            title=snapshot.title or "nomadnomad-job",
            listing_html=listing_html,
            listing_snapshot_json=snapshot.model_dump_json(),
        ),
    )


async def resolve_project_and_snapshot(
    connection: aiosqlite.Connection,
    *,
    listing_html: str | None,
    job_posting_snapshot: JobPostingSnapshot | None,
    project_id: int | None,
) -> tuple[int, JobPostingSnapshot]:
    validate_exactly_one_job_source(
        listing_html=listing_html,
        job_posting_snapshot=job_posting_snapshot,
        project_id=project_id,
    )

    if project_id is not None:
        row = await ProjectRepo.get_by_id(connection, project_id)
        if row is None:
            raise ValueError(f"project_id={project_id} not found")
        raw_snapshot = row["listing_snapshot_json"]
        if not raw_snapshot:
            raise ValueError(f"project_id={project_id} has no listing_snapshot_json")
        return project_id, JobPostingSnapshot.model_validate_json(raw_snapshot)

    if listing_html is not None:
        snapshot = parse_upwork_job_html(listing_html)
        new_project_id = await insert_project_for_snapshot(connection, snapshot=snapshot, listing_html=listing_html)
        return new_project_id, snapshot

    assert job_posting_snapshot is not None
    snapshot = job_posting_snapshot
    new_project_id = await insert_project_for_snapshot(connection, snapshot=snapshot, listing_html=None)
    return new_project_id, snapshot


async def persist_requirement_analysis(
    connection: aiosqlite.Connection,
    *,
    project_id: int,
    analysis: RequirementAnalysis,
) -> int:
    return await RequirementAnalysisRepo.insert(
        connection,
        project_id=project_id,
        analysis=analysis,
    )


async def persist_proposal(
    connection: aiosqlite.Connection,
    *,
    project_id: int,
    proposal: Proposal,
) -> int:
    return await ProposalRepo.insert(
        connection,
        project_id=project_id,
        proposal=proposal,
    )
