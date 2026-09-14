"""Seed idempotente das dimensoes fixas (dim_tempo, dim_setor, dim_tecnologia, etc.)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-14
"""
from __future__ import annotations

from alembic import op

from db.migrations._sql_utils import run_sql_file

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("db", "seeds", "seed_dimensoes.sql")


def downgrade() -> None:
    # Seed e composto so por dimensoes fixas/calendario: removidas junto do
    # downgrade da 0001 (DROP SCHEMA core CASCADE). Nada a fazer aqui.
    op.execute("SELECT 1")
