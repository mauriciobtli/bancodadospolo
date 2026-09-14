"""Loader generico de CSV para qualquer tabela raw.*

O CSV de origem pode ter nomes de coluna diferentes dos esperados pela
tabela raw — `mapeamento_colunas` traduz "coluna do arquivo" -> "coluna raw".
Colunas do arquivo que nao estiverem no mapeamento sao ignoradas.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Connection

from etl.execucao import RegistroExecucao, iniciar_execucao
from etl.loaders.base import inserir_dataframe_em_raw, ler_csv


def carregar_csv_para_raw(
    conn: Connection,
    caminho: Path,
    tabela_raw: str,
    entidade_alvo: str,
    mapeamento_colunas: dict[str, str],
) -> RegistroExecucao:
    execucao = iniciar_execucao(conn, arquivo_fonte=str(caminho), tipo_fonte="csv", entidade_alvo=entidade_alvo)
    df = ler_csv(caminho)
    df = df.rename(columns=mapeamento_colunas)
    colunas_validas = [c for c in mapeamento_colunas.values() if c in df.columns]
    df = df[colunas_validas]
    inserir_dataframe_em_raw(conn, df, tabela_raw, execucao, arquivo_origem=str(caminho))
    return execucao
