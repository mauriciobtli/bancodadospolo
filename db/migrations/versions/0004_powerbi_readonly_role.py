"""Role read-only powerbi_readonly, restrita ao schema mart

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-14
"""
from __future__ import annotations

from alembic import op

from db.migrations._sql_utils import run_sql_file

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("db", "roles", "powerbi_readonly.sql")


def downgrade() -> None:
    # Nao derruba a role automaticamente (pode estar em uso por conexoes
    # ativas do Power BI); revoga apenas os privilegios concedidos.
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA mart FROM powerbi_readonly")
    op.execute("REVOKE USAGE ON SCHEMA mart FROM powerbi_readonly")
