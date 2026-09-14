"""Loader de Google Sheets.

Implementacao inicial: planilhas publicadas na web como CSV
(Arquivo > Compartilhar > Publicar na web > CSV). Isso evita depender de
credenciais de service account so para a leitura de planilhas publicas,
mantendo o ETL simples.

Para planilhas privadas, o caminho preparado (nao implementado nesta
primeira versao) e usar uma service account do Google (variavel de
ambiente POLO_GSHEETS_CREDENTIALS_FILE, ja reservada no .env.example) com
a biblioteca `gspread`, mantendo a mesma assinatura de
`carregar_google_sheet_para_raw` — a credencial NUNCA deve ser commitada.
"""
from __future__ import annotations

from sqlalchemy.engine import Connection

from etl.execucao import RegistroExecucao, iniciar_execucao
from etl.loaders.base import inserir_dataframe_em_raw
from etl.loaders.base import ler_csv  # reutilizado apos o download


def montar_url_csv_publico(sheet_id: str, gid: str = "0") -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def carregar_google_sheet_para_raw(
    conn: Connection,
    sheet_id: str,
    tabela_raw: str,
    entidade_alvo: str,
    mapeamento_colunas: dict[str, str],
    gid: str = "0",
) -> RegistroExecucao:
    import pandas as pd

    url = montar_url_csv_publico(sheet_id, gid)
    execucao = iniciar_execucao(conn, arquivo_fonte=url, tipo_fonte="google_sheets", entidade_alvo=entidade_alvo)

    df = pd.read_csv(url, dtype=str, keep_default_na=False, na_values=["", "NA", "N/A", "null"])
    df = df.astype(object).where(pd.notnull(df), None)
    df = df.rename(columns=mapeamento_colunas)
    colunas_validas = [c for c in mapeamento_colunas.values() if c in df.columns]
    df = df[colunas_validas]

    inserir_dataframe_em_raw(conn, df, tabela_raw, execucao, arquivo_origem=url)
    return execucao


__all__ = ["montar_url_csv_publico", "carregar_google_sheet_para_raw", "ler_csv"]
