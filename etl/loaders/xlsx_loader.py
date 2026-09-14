"""Loader generico de XLSX para qualquer tabela raw.* (mesma logica do CSV)."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Connection

from etl.execucao import RegistroExecucao, iniciar_execucao
from etl.loaders.base import inserir_dataframe_em_raw, ler_xlsx


def carregar_xlsx_para_raw(
    conn: Connection,
    caminho: Path,
    tabela_raw: str,
    entidade_alvo: str,
    mapeamento_colunas: dict[str, str],
    sheet_name: str | int = 0,
) -> RegistroExecucao:
    execucao = iniciar_execucao(conn, arquivo_fonte=str(caminho), tipo_fonte="xlsx", entidade_alvo=entidade_alvo)
    df = ler_xlsx(caminho, sheet_name=sheet_name)
    df = df.rename(columns=mapeamento_colunas)
    colunas_validas = [c for c in mapeamento_colunas.values() if c in df.columns]
    df = df[colunas_validas]
    inserir_dataframe_em_raw(conn, df, tabela_raw, execucao, arquivo_origem=str(caminho))
    return execucao
