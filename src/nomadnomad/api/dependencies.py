"""FastAPI 依赖注入：数据库连接与 LLM 客户端。

Story 7 会在路由层通过依赖注入获取这些对象；测试可通过 ``dependency_overrides`` 注入 fake。
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, cast

import aiosqlite
from fastapi import Request

from nomadnomad.agents.llm.json_chat_client import OpenAiCompatibleJsonChatClient
from nomadnomad.config.llm_settings import LlmSettings
from nomadnomad.db.connection import connect_file, connect_memory, init_schema


@asynccontextmanager
async def open_sqlite_connection() -> AsyncIterator[aiosqlite.Connection]:
    """按环境变量打开 SQLite 连接，并确保 schema 初始化。"""
    database_path = os.environ.get("NOMADNOMAD_SQLITE_PATH", "data/nomadnomad.sqlite")
    if database_path == ":memory:":
        async with connect_memory() as connection:
            await init_schema(connection)
            yield connection
        return

    async with connect_file(database_path) as connection:
        await init_schema(connection)
        yield connection


def get_db_connection(request: Request) -> aiosqlite.Connection:
    """从 app.state 取出共享连接（由 lifespan 创建）。"""
    # getattr 会返回 Any；这里显式 cast，避免 mypy no-any-return
    connection = cast(aiosqlite.Connection | None, getattr(request.app.state, "db_connection", None))
    if connection is None:
        raise RuntimeError("db_connection is not initialized; did you forget to configure lifespan?")
    return connection


def get_llm_client() -> OpenAiCompatibleJsonChatClient:
    """默认 LLM 客户端（真实 HTTP）；测试建议 override。"""
    return OpenAiCompatibleJsonChatClient(LlmSettings())
