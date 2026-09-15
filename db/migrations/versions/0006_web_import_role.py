"""Role web_import: privilegio minimo para a importacao disparada pela tela
web, separada da role de administracao (POLO_DB_USER) usada pelo ETL de
linha de comando e da role django_app usada pelo restante do admin web.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-15
"""
from __future__ import annotations

from alembic import op

from db.migrations._sql_utils import run_sql_file

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("db", "roles", "web_import.sql")


def downgrade() -> None:
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA raw FROM web_import")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA core FROM web_import")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA etl FROM web_import")
    op.execute("REVOKE USAGE ON SCHEMA raw FROM web_import")
    op.execute("REVOKE USAGE ON SCHEMA core FROM web_import")
    op.execute("REVOKE USAGE ON SCHEMA etl FROM web_import")
