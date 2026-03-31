"""FastAPI 应用入口与启动."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite
from fastapi import FastAPI

from nomadnomad.api.dependencies import open_sqlite_connection
from nomadnomad.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期：启动时初始化，关闭时清理."""
    connection: aiosqlite.Connection | None = None
    async with open_sqlite_connection() as opened:
        connection = opened
        app.state.db_connection = connection
        yield
    # 连接关闭由 open_sqlite_connection 管理；这里仅保证 state 不残留
    if hasattr(app.state, "db_connection"):
        delattr(app.state, "db_connection")


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
