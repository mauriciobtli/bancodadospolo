"""Configuracao central do ETL.

Nenhuma credencial vive neste arquivo ou em qualquer arquivo versionado:
tudo vem de variaveis de ambiente (carregadas de um .env local, fora do
git — ver .env.example). Isso evita vazamento de segredo pelo repositorio.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: str
    dbname: str
    user: str
    password: str


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Variavel de ambiente obrigatoria '{name}' nao definida. "
            "Copie .env.example para .env e preencha os valores."
        )
    return value


def get_admin_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host=os.environ.get("POLO_DB_HOST", "localhost"),
        port=os.environ.get("POLO_DB_PORT", "5432"),
        dbname=_require_env("POLO_DB_NAME"),
        user=_require_env("POLO_DB_USER"),
        password=_require_env("POLO_DB_PASSWORD"),
    )


def get_readonly_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host=os.environ.get("POLO_DB_HOST", "localhost"),
        port=os.environ.get("POLO_DB_PORT", "5432"),
        dbname=_require_env("POLO_DB_NAME"),
        user=_require_env("POLO_BI_DB_USER"),
        password=_require_env("POLO_BI_DB_PASSWORD"),
    )


def build_database_url(readonly: bool = False) -> str:
    settings = get_readonly_settings() if readonly else get_admin_settings()
    return (
        f"postgresql+psycopg://{settings.user}:{settings.password}"
        f"@{settings.host}:{settings.port}/{settings.dbname}"
    )


def quarantine_dir() -> Path:
    raw = os.environ.get("POLO_ETL_QUARANTINE_DIR", "etl/quarantine")
    path = PROJECT_ROOT / raw
    path.mkdir(parents=True, exist_ok=True)
    return path
