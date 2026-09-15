"""Extrai uma mensagem de erro legivel de uma excecao do banco (IntegrityError
do psycopg/Postgres). Fica fora do pacote core_admin.admin para evitar
import circular com core_admin.admin_site (importado por admin_site.py)."""
from __future__ import annotations


def mensagem_amigavel(exc: Exception) -> str:
    causa = exc.__cause__ or exc
    texto = str(causa).strip()
    if not texto:
        return "O banco de dados rejeitou os dados informados."
    return texto.splitlines()[0]
