"""Story 7：提案查询 API。"""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from nomadnomad.api.dependencies import get_db_connection
from nomadnomad.db.repositories import ProposalRepo
from nomadnomad.models import Proposal

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ProposalDetailResponse(BaseModel):
    id: int
    project_id: int
    created_at: str
    title: str
    body_markdown: str


@router.get("/{proposal_id}", response_model=ProposalDetailResponse)
async def get_proposal(
    proposal_id: int,
    connection: aiosqlite.Connection = Depends(get_db_connection),
) -> ProposalDetailResponse:
    row = await ProposalRepo.get_by_id(connection, proposal_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"proposal_id={proposal_id} not found")

    proposal = Proposal.model_validate_json(row["proposal_json"])
    return ProposalDetailResponse(
        id=int(row["id"]),
        project_id=int(row["project_id"]),
        created_at=str(row["created_at"]),
        title=proposal.title,
        body_markdown=proposal.body_markdown,
    )
