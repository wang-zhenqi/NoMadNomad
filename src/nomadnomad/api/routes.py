"""API 路由定义（使用 APIRouter，在 create_app 中 include_router 注册）."""

from fastapi import APIRouter

router = APIRouter(tags=["general"])


@router.get("/health")
async def health() -> dict[str, str]:
    """健康检查."""
    return {"status": "ok"}
