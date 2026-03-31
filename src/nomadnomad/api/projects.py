"""Story 7：项目相关 API（创建项目、触发分析、触发提案生成、查询项目）。"""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from nomadnomad.agents.llm.json_chat_client import JsonCompletionClient
from nomadnomad.agents.proposal_generation_agent import run_proposal_generation_agent
from nomadnomad.agents.requirement_analysis_agent import run_requirement_analysis_agent
from nomadnomad.api.dependencies import get_db_connection, get_llm_client
from nomadnomad.db.repositories import ProjectRepo, ProposalRepo, RequirementAnalysisRepo
from nomadnomad.ingest import parse_upwork_job_html
from nomadnomad.models import JobPostingSnapshot
from nomadnomad.services.analyze_proposal_use_case import (
    insert_project_for_snapshot,
    persist_proposal,
    persist_requirement_analysis,
)

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    listing_html: str | None = None
    title: str | None = None
    original_description: str | None = None
    job_posting_snapshot: JobPostingSnapshot | None = None


class CreateProjectResponse(BaseModel):
    project_id: int


class AnalyzeProjectResponse(BaseModel):
    requirement_analysis_id: int


class CreateProposalResponse(BaseModel):
    proposal_id: int


class ProjectDetailResponse(BaseModel):
    id: int
    title: str | None
    created_at: str
    listing_snapshot: JobPostingSnapshot | None
    latest_requirement_analysis_id: int | None
    latest_proposal_id: int | None


def _validate_create_project_request(payload: CreateProjectRequest) -> None:
    if payload.listing_html is not None:
        return
    if payload.job_posting_snapshot is not None:
        return
    if payload.title is not None and payload.original_description is not None:
        return
    raise HTTPException(
        status_code=422,
        detail="Provide either listing_html, job_posting_snapshot, or (title + original_description).",
    )


@router.post("", response_model=CreateProjectResponse)
async def create_project(
    payload: CreateProjectRequest,
    connection: aiosqlite.Connection = Depends(get_db_connection),
) -> CreateProjectResponse:
    _validate_create_project_request(payload)

    listing_html = payload.listing_html
    if listing_html is not None:
        snapshot = parse_upwork_job_html(listing_html)
        project_id = await insert_project_for_snapshot(connection, snapshot=snapshot, listing_html=listing_html)
        return CreateProjectResponse(project_id=project_id)

    if payload.job_posting_snapshot is not None:
        snapshot = payload.job_posting_snapshot
        project_id = await insert_project_for_snapshot(connection, snapshot=snapshot, listing_html=None)
        return CreateProjectResponse(project_id=project_id)

    snapshot = JobPostingSnapshot(
        source_type="free_text",
        title=payload.title,
        summary_text=payload.original_description,
    )
    project_id = await insert_project_for_snapshot(connection, snapshot=snapshot, listing_html=None)
    return CreateProjectResponse(project_id=project_id)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: int,
    connection: aiosqlite.Connection = Depends(get_db_connection),
) -> ProjectDetailResponse:
    row = await ProjectRepo.get_by_id(connection, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"project_id={project_id} not found")

    raw_snapshot = row.get("listing_snapshot_json")
    listing_snapshot = JobPostingSnapshot.model_validate_json(raw_snapshot) if raw_snapshot else None

    latest_ra_id = await RequirementAnalysisRepo.get_latest_id_for_project(connection, project_id=project_id)
    latest_prop_id = await ProposalRepo.get_latest_id_for_project(connection, project_id=project_id)

    return ProjectDetailResponse(
        id=int(row["id"]),
        title=row.get("title"),
        created_at=str(row["created_at"]),
        listing_snapshot=listing_snapshot,
        latest_requirement_analysis_id=latest_ra_id,
        latest_proposal_id=latest_prop_id,
    )


@router.post("/{project_id}/analyze", response_model=AnalyzeProjectResponse)
async def analyze_project(
    project_id: int,
    connection: aiosqlite.Connection = Depends(get_db_connection),
    llm_client: JsonCompletionClient = Depends(get_llm_client),
) -> AnalyzeProjectResponse:
    row = await ProjectRepo.get_by_id(connection, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"project_id={project_id} not found")
    raw_snapshot = row.get("listing_snapshot_json")
    if not raw_snapshot:
        raise HTTPException(status_code=400, detail=f"project_id={project_id} has no listing_snapshot_json")

    snapshot = JobPostingSnapshot.model_validate_json(raw_snapshot)
    outcome = await run_requirement_analysis_agent(
        connection,
        project_id=project_id,
        snapshot=snapshot,
        llm_client=llm_client,
        trace_id=None,
    )
    if outcome.analysis is None:
        raise HTTPException(status_code=502, detail=outcome.error_message or "requirement_analysis_failed")

    analysis_id = await persist_requirement_analysis(connection, project_id=project_id, analysis=outcome.analysis)
    return AnalyzeProjectResponse(requirement_analysis_id=analysis_id)


@router.post("/{project_id}/proposals", response_model=CreateProposalResponse)
async def create_proposal(
    project_id: int,
    connection: aiosqlite.Connection = Depends(get_db_connection),
    llm_client: JsonCompletionClient = Depends(get_llm_client),
) -> CreateProposalResponse:
    row = await ProjectRepo.get_by_id(connection, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"project_id={project_id} not found")

    latest_ra_id = await RequirementAnalysisRepo.get_latest_id_for_project(connection, project_id=project_id)
    if latest_ra_id is None:
        raise HTTPException(status_code=409, detail=f"project_id={project_id} has no requirement analysis yet")

    outcome = await run_proposal_generation_agent(
        connection,
        project_id=project_id,
        requirement_analysis_id=latest_ra_id,
        llm_client=llm_client,
        trace_id=None,
    )
    if outcome.proposal is None:
        raise HTTPException(status_code=502, detail=outcome.error_message or "proposal_generation_failed")

    proposal_id = await persist_proposal(connection, project_id=project_id, proposal=outcome.proposal)
    return CreateProposalResponse(proposal_id=proposal_id)
