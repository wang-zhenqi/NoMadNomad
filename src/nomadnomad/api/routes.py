"""API 路由定义（使用 APIRouter，在 create_app 中 include_router 注册）."""

from fastapi import APIRouter

from nomadnomad.api.projects import router as projects_router
from nomadnomad.api.proposals import router as proposals_router

router = APIRouter(tags=["general"])
router.include_router(projects_router)
router.include_router(proposals_router)


@router.get("/health")
async def health() -> dict[str, str]:
    """健康检查."""
    return {"status": "ok"}
