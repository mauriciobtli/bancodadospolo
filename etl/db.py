"""Factory de engine SQLAlchemy para o ETL (sempre usa a conexao de admin,
nunca a role read-only do Power BI — o ETL precisa escrever em raw/core/etl)."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine

from etl.config import build_database_url


def get_engine(echo: bool = False) -> Engine:
    return create_engine(build_database_url(readonly=False), echo=echo, future=True)
