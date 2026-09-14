"""Fixtures compartilhadas.

Os testes em tests/db e tests/mart exigem um Postgres real com as
migrations aplicadas (ver README — `docker compose up -d && alembic
upgrade head`). Cada teste roda dentro de uma transacao que e sempre
revertida no final (rollback), entao nenhum teste deixa dado residual no
banco, mesmo os que gravam nas tabelas.
"""
from __future__ import annotations

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import Connection

from etl.config import build_database_url


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    return create_engine(build_database_url(readonly=False), future=True)


@pytest.fixture()
def db_conn(db_engine: Engine) -> Connection:
    connection = db_engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()
