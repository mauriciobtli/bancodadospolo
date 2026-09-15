"""Mesmo teste de ponta a ponta do pipeline de organizacoes, mas para XLSX
(usado pela tela de importacao do admin web) — garante que o loader XLSX
produz o mesmo resultado que o loader CSV para os mesmos dados."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from etl.config import PROJECT_ROOT
from etl.pipeline import carregar_organizacoes_xlsx, processar_organizacoes

CAMINHO_CSV_EXEMPLO = PROJECT_ROOT / "data" / "samples" / "organizacoes_exemplo.csv"


def test_pipeline_organizacoes_xlsx_carrega_valida_e_rejeita(db_conn, tmp_path):
    caminho_xlsx = tmp_path / "organizacoes_exemplo.xlsx"
    pd.read_csv(CAMINHO_CSV_EXEMPLO, dtype=str).to_excel(caminho_xlsx, index=False)

    execucao = carregar_organizacoes_xlsx(db_conn, caminho_xlsx)
    processar_organizacoes(db_conn, execucao)
    execucao.finalizar(status="sucesso_parcial" if execucao.registros_rejeitados else "sucesso")

    assert execucao.registros_lidos == 5
    assert execucao.registros_inseridos == 3
    assert execucao.registros_rejeitados == 2

    orgs = db_conn.execute(
        text("SELECT nome FROM core.dim_organizacao WHERE fonte_dado = :fonte ORDER BY nome"),
        {"fonte": str(caminho_xlsx)},
    ).scalars().all()
    assert "Alfa Tecnologia Ltda" in orgs
    assert "Beta Startup" in orgs
    assert "Instituto Gama de Pesquisa" in orgs
