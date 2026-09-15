"""Factories de engine SQLAlchemy para o ETL.

get_engine(): sempre usa a conexao de administracao (POLO_DB_USER), nunca
a role read-only do Power BI — para o ETL de linha de comando, rodado por
um operador de confianca com acesso total ao schema.

get_web_import_engine(): usa a role dedicada e minima web_import (ver
db/roles/web_import.sql) — para a importacao disparada pela tela web
(webapp/importacao/views.py), que roda dentro de um processo exposto a
upload de usuario autenticado e por isso NUNCA deve ter o privilegio de
administracao do POLO_DB_USER.
"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine

from etl.config import build_database_url, build_web_import_database_url


def get_engine(echo: bool = False) -> Engine:
    return create_engine(build_database_url(readonly=False), echo=echo, future=True)


def get_web_import_engine(echo: bool = False) -> Engine:
    return create_engine(build_web_import_database_url(), echo=echo, future=True)
