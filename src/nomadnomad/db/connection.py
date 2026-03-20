"""aiosqlite 连接与 Schema 初始化（可重复执行，本地/CI 一致）。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from nomadnomad.db.ddl import SCHEMA_SQL


def _configure_connection(connection: aiosqlite.Connection) -> None:
    connection.row_factory = aiosqlite.Row


async def _apply_pragmas(connection: aiosqlite.Connection) -> None:
    await connection.execute("PRAGMA foreign_keys = ON")


@asynccontextmanager
async def connect_memory() -> AsyncIterator[aiosqlite.Connection]:
    """打开内存库连接；退出时关闭。适合测试与无文件副作用场景。"""
    connection = await aiosqlite.connect(":memory:")
    _configure_connection(connection)
    await _apply_pragmas(connection)
    try:
        yield connection
    finally:
        await connection.close()


@asynccontextmanager
async def connect_file(database_path: str | Path) -> AsyncIterator[aiosqlite.Connection]:
    """打开磁盘上的 SQLite 文件；父目录不存在时会创建。退出时关闭。"""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = await aiosqlite.connect(str(path))
    _configure_connection(connection)
    await _apply_pragmas(connection)
    try:
        yield connection
    finally:
        await connection.close()


async def init_schema(connection: aiosqlite.Connection) -> None:
    """执行 DDL（CREATE TABLE IF NOT EXISTS）。同一连接可安全重复调用。"""
    _configure_connection(connection)
    await connection.executescript(SCHEMA_SQL)
    await connection.commit()
