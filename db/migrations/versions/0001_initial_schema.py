"""Schemas, funcoes, controle de ETL, raw e core (dimensoes, projeto, fatos, bridges)

Revision ID: 0001
Revises:
Create Date: 2026-09-14
"""
from __future__ import annotations

from alembic import op

from db.migrations._sql_utils import run_sql_file

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("db", "schemas", "00_schemas.sql")
    run_sql_file("db", "schemas", "01_funcoes.sql")
    run_sql_file("db", "schemas", "10_etl_controle.sql")
    run_sql_file("db", "schemas", "12_raw.sql")
    run_sql_file("db", "schemas", "20_core_dimensoes.sql")
    run_sql_file("db", "schemas", "21_core_projeto.sql")
    run_sql_file("db", "schemas", "22_core_fatos.sql")
    run_sql_file("db", "schemas", "23_core_bridges.sql")
    run_sql_file("db", "schemas", "24_core_cobertura.sql")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS raw CASCADE")
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")
    op.execute("DROP SCHEMA IF EXISTS etl CASCADE")
