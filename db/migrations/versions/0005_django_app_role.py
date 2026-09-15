"""Schema app + role django_app, para a camada administrativa web (Django)

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-15
"""
from __future__ import annotations

from alembic import op

from db.migrations._sql_utils import run_sql_file

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("db", "roles", "django_app.sql")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS app CASCADE")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA core FROM django_app")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA etl FROM django_app")
    op.execute("REVOKE USAGE ON SCHEMA core FROM django_app")
    op.execute("REVOKE USAGE ON SCHEMA etl FROM django_app")
