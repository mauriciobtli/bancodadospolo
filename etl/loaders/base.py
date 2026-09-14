"""Leitura tolerante de planilhas (CSV/XLSX) para DataFrame de texto puro.

Le tudo como string (dtype=str): tipagem/validacao e responsabilidade da
camada de transformacao (etl/transforms, etl/validators), nunca do loader.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from etl.execucao import RegistroExecucao

_NA_VALUES = ["", "NA", "N/A", "null", "NULL", "-"]


def ler_csv(caminho: Path, **kwargs) -> pd.DataFrame:
    df = pd.read_csv(caminho, dtype=str, keep_default_na=False, na_values=_NA_VALUES, **kwargs)
    return df.astype(object).where(pd.notnull(df), None)


def ler_xlsx(caminho: Path, sheet_name: str | int = 0, **kwargs) -> pd.DataFrame:
    df = pd.read_excel(
        caminho, sheet_name=sheet_name, dtype=str, keep_default_na=False,
        na_values=_NA_VALUES, engine="openpyxl", **kwargs,
    )
    return df.astype(object).where(pd.notnull(df), None)


def inserir_dataframe_em_raw(
    conn: Connection,
    df: pd.DataFrame,
    tabela_raw: str,
    execucao: RegistroExecucao,
    arquivo_origem: str,
) -> None:
    """Insere cada linha do DataFrame na tabela raw.<tabela_raw>, marcando
    id_execucao/linha_origem/arquivo_origem para rastreabilidade."""
    colunas = list(df.columns)
    colunas_sql = ", ".join(colunas + ["id_execucao", "linha_origem", "arquivo_origem"])
    parametros_sql = ", ".join(f":{c}" for c in colunas) + ", :id_execucao, :linha_origem, :arquivo_origem"
    stmt = text(f"INSERT INTO raw.{tabela_raw} ({colunas_sql}) VALUES ({parametros_sql})")

    linhas = []
    for indice, linha in df.iterrows():
        parametros = {c: linha[c] for c in colunas}
        parametros["id_execucao"] = execucao.id_execucao
        parametros["linha_origem"] = int(indice) + 2  # +2: cabecalho (1) + indice 0-based
        parametros["arquivo_origem"] = arquivo_origem
        linhas.append(parametros)

    if linhas:
        conn.execute(stmt, linhas)
    execucao.registros_lidos += len(linhas)
