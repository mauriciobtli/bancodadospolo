"""Schema mart: dimensoes, fatos, KPIs, rede e views de apoio ao Power BI

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-14
"""
from __future__ import annotations

from alembic import op

from db.migrations._sql_utils import run_sql_file

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("db", "schemas", "30_mart_dimensoes.sql")
    run_sql_file("db", "schemas", "31_mart_fatos.sql")
    run_sql_file("db", "schemas", "32_mart_kpis.sql")
    run_sql_file("db", "schemas", "33_mart_rede.sql")
    run_sql_file("db", "schemas", "34_mart_powerbi.sql")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS mart CASCADE")
    op.execute("CREATE SCHEMA IF NOT EXISTS mart")
