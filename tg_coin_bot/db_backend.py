"""Абстракция БД: SQLite (локально) или MySQL (Railway / MYSQL_URL, DATABASE_URL)."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse

import aiosqlite
import aiomysql
from aiomysql.cursors import DictCursor

__all__ = [
    "close_db_backend",
    "db_session",
    "init_db_backend",
    "is_mysql",
    "row_to_dict",
]

_mysql_pool: Optional[Any] = None
_sqlite_path: str = ""
_use_mysql: bool = False


def is_mysql() -> bool:
    return _use_mysql


def _mysql_dsn_from_env() -> Optional[str]:
    for key in ("MYSQL_URL", "DATABASE_URL"):
        v = os.getenv(key, "").strip()
        if not v:
            continue
        if v.startswith("mysql://") or v.startswith("mysql+pymysql://"):
            return v
    return None


def _parse_mysql_url(url: str) -> dict[str, Any]:
    u = url.strip()
    if u.startswith("mysql+pymysql://"):
        u = "mysql://" + u[len("mysql+pymysql://") :]
    if not u.startswith("mysql://"):
        raise ValueError("Ожидался URL вида mysql://...")
    parsed = urlparse(u)
    path = (parsed.path or "").lstrip("/")
    db_name = path.split("?", 1)[0] if path else ""
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "db": db_name,
    }


class _MysqlDb:
    def __init__(self, conn: Any) -> None:
        self._conn = conn
        self._cur: Any = None

    async def _close_cursor(self) -> None:
        if self._cur is not None:
            await self._cur.close()
            self._cur = None

    async def execute(self, sql: str, parameters: Any = ()) -> Any:
        if parameters is None:
            parameters = ()
        await self._close_cursor()
        self._cur = await self._conn.cursor(DictCursor)
        sql_exec = sql.replace("?", "%s")
        await self._cur.execute(sql_exec, parameters)
        return self._cur

    async def commit(self) -> None:
        await self._conn.commit()


async def init_db_backend(db_path: str) -> None:
    global _mysql_pool, _sqlite_path, _use_mysql

    # Повторный вызов безопасен: не плодим второй MySQL pool и не перетираем путь к SQLite.
    if _mysql_pool is not None:
        return
    if _sqlite_path:
        return

    dsn = _mysql_dsn_from_env()
    if dsn:
        _use_mysql = True
        cfg = _parse_mysql_url(dsn)
        _mysql_pool = await aiomysql.create_pool(
            host=cfg["host"],
            port=int(cfg["port"]),
            user=cfg["user"],
            password=cfg["password"],
            db=cfg["db"],
            autocommit=False,
            minsize=1,
            maxsize=10,
        )
        _sqlite_path = ""
        return

    _use_mysql = False
    p = Path(db_path)
    _sqlite_path = str(p if p.is_absolute() else Path(__file__).resolve().parent / p)


async def close_db_backend() -> None:
    global _mysql_pool
    if _mysql_pool is not None:
        _mysql_pool.close()
        await _mysql_pool.wait_closed()
        _mysql_pool = None


@asynccontextmanager
async def db_session() -> AsyncIterator[Any]:
    if _use_mysql:
        if _mysql_pool is None:
            raise RuntimeError("MySQL pool не инициализирован: вызови init_db_backend.")
        async with _mysql_pool.acquire() as conn:
            db = _MysqlDb(conn)
            try:
                yield db
            finally:
                await db._close_cursor()
    else:
        async with aiosqlite.connect(_sqlite_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn


def row_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        raise TypeError("row_to_dict: row is None")
    if isinstance(row, dict):
        return dict(row)
    if isinstance(row, Mapping):
        return dict(row)
    return dict(row)
