"""FastAPI 应用入口与启动."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from nomadnomad.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期：启动时初始化，关闭时清理."""
    yield


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例."""
    app = FastAPI(
        title="NoMadNomad API",
        description="AI 驱动的自由职业者全流程项目管理 API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()


def run_api() -> None:
    """供 Poetry script 调用：启动 uvicorn."""
    import uvicorn

    uvicorn.run(
        "nomadnomad.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
