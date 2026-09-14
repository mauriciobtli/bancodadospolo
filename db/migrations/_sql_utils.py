"""Helpers para migrations que aplicam DDL versionado como arquivos .sql puros.

Mantemos o DDL em db/schemas, db/seeds e db/roles como SQL legivel e
comentado (facilita revisao/DBA), e as migrations apenas orquestram a
ordem de aplicacao de forma idempotente e versionada pelo Alembic.
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_sql_file(*relative_path_parts: str) -> None:
    path = PROJECT_ROOT.joinpath(*relative_path_parts)
    sql = path.read_text(encoding="utf-8")
    op.execute(sql)
