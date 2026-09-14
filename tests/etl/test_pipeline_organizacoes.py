"""Teste de ponta a ponta do pipeline de organizacoes: CSV -> raw -> core,
com validacao de CNPJ, dominio, deduplicacao e quarentena."""
from __future__ import annotations

from sqlalchemy import text

from etl.config import PROJECT_ROOT
from etl.pipeline import carregar_organizacoes_csv, processar_organizacoes

CAMINHO_EXEMPLO = PROJECT_ROOT / "data" / "samples" / "organizacoes_exemplo.csv"


def test_pipeline_organizacoes_carrega_valida_e_rejeita(db_conn):
    execucao = carregar_organizacoes_csv(db_conn, CAMINHO_EXEMPLO)
    processar_organizacoes(db_conn, execucao)
    execucao.finalizar(status="sucesso_parcial" if execucao.registros_rejeitados else "sucesso")

    assert execucao.registros_lidos == 5
    assert execucao.registros_inseridos == 3  # Alfa, Beta, Gama
    assert execucao.registros_rejeitados == 2  # CNPJ invalido + tipo fora do dominio

    orgs = db_conn.execute(
        text("SELECT nome, cnpj FROM core.dim_organizacao WHERE fonte_dado = :fonte ORDER BY nome"),
        {"fonte": str(CAMINHO_EXEMPLO)},
    ).all()
    nomes = [row.nome for row in orgs]
    assert "Alfa Tecnologia Ltda" in nomes
    assert "Beta Startup" in nomes
    assert "Instituto Gama de Pesquisa" in nomes

    contatos = db_conn.execute(text("SELECT count(*) FROM core.contato_organizacao")).scalar_one()
    assert contatos == 2  # Alfa e Beta tem contato preenchido; Gama nao

    motivos = db_conn.execute(
        text(
            "SELECT motivo_rejeicao FROM etl.quarentena_registro WHERE id_execucao = :id_execucao ORDER BY id_quarentena"
        ),
        {"id_execucao": execucao.id_execucao},
    ).scalars().all()
    assert any("cnpj" in m.lower() for m in motivos)
    assert any("tipo_organizacao" in m.lower() for m in motivos)

    execucao_row = db_conn.execute(
        text("SELECT status, registros_lidos, registros_rejeitados FROM etl.etl_execucao WHERE id_execucao = :id"),
        {"id": execucao.id_execucao},
    ).first()
    assert execucao_row.status == "sucesso_parcial"
    assert execucao_row.registros_lidos == 5
    assert execucao_row.registros_rejeitados == 2
