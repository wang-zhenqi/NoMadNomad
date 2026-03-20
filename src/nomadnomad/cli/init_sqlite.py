"""对磁盘 SQLite 执行 DDL，便于本地/部署一键建表（Story 3）。"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from nomadnomad.db.connection import connect_file, init_schema


async def _run(database_path: Path) -> None:
    async with connect_file(database_path) as connection:
        await init_schema(connection)


def main() -> None:
    default_path = os.environ.get("NOMADNOMAD_SQLITE_PATH", "data/nomadnomad.sqlite")
    parser = argparse.ArgumentParser(description="初始化 NoMadNomad SQLite 表结构（幂等）。")
    parser.add_argument(
        "database_path",
        nargs="?",
        default=default_path,
        help=f"数据库文件路径（默认: {default_path}，可被环境变量 NOMADNOMAD_SQLITE_PATH 覆盖）",
    )
    arguments = parser.parse_args()
    asyncio.run(_run(Path(arguments.database_path)))


if __name__ == "__main__":
    main()
