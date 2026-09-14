"""Deduplicacao de organizacoes.

Regra: CNPJ valido e a chave primaria de deduplicacao (duas linhas com o
mesmo CNPJ sao a mesma organizacao). Na ausencia de CNPJ (associacoes
informais, coletivos), usa nome normalizado + municipio como chave de
fallback — mais fraca, mas evita duplicar entradas obvias vindas de
planilhas diferentes.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Connection

from etl.transforms.normalizacao import normalizar_nome_organizacao
from etl.validators.cnpj import is_valid_cnpj, normalize_cnpj


@dataclass(frozen=True)
class ChaveDeduplicacao:
    tipo: str  # "cnpj" ou "nome_municipio"
    valor: str


def calcular_chave(cnpj: str | None, nome: str | None, id_municipio: int | None) -> ChaveDeduplicacao | None:
    cnpj_normalizado = normalize_cnpj(cnpj)
    if cnpj_normalizado and is_valid_cnpj(cnpj_normalizado):
        return ChaveDeduplicacao(tipo="cnpj", valor=cnpj_normalizado)

    nome_normalizado = normalizar_nome_organizacao(nome)
    if nome_normalizado is None:
        return None
    municipio_parte = str(id_municipio) if id_municipio is not None else "sem_municipio"
    return ChaveDeduplicacao(tipo="nome_municipio", valor=f"{nome_normalizado}|{municipio_parte}")


def buscar_organizacao_existente(
    conn: Connection, cnpj: str | None, nome: str | None, id_municipio: int | None
) -> int | None:
    """Retorna id_organizacao existente que corresponda a chave de dedup, ou None."""
    chave = calcular_chave(cnpj, nome, id_municipio)
    if chave is None:
        return None

    if chave.tipo == "cnpj":
        row = conn.execute(
            text("SELECT id_organizacao FROM core.dim_organizacao WHERE cnpj = :cnpj"),
            {"cnpj": chave.valor},
        ).first()
        return row[0] if row else None

    nome_normalizado, _, municipio_parte = chave.valor.partition("|")
    id_municipio_busca = None if municipio_parte == "sem_municipio" else int(municipio_parte)
    row = conn.execute(
        text(
            """
            SELECT id_organizacao FROM core.dim_organizacao
            WHERE cnpj IS NULL
              AND lower(regexp_replace(unaccent(nome), '[^a-zA-Z0-9\\s]', '', 'g')) = :nome_normalizado
              AND id_municipio IS NOT DISTINCT FROM :id_municipio
            """
        ),
        {"nome_normalizado": nome_normalizado, "id_municipio": id_municipio_busca},
    ).first()
    return row[0] if row else None
