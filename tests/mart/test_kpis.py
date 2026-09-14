"""Testes das views de KPI em mart: nenhuma deve estourar erro de divisao
por zero — o resultado esperado nesse caso e NULL (via NULLIF)."""
from __future__ import annotations

from sqlalchemy import text

ID_TEMPO_EXEMPLO = 20220101


def _criar_organizacao(conn, nome: str = "Organizacao KPI") -> int:
    row = conn.execute(
        text(
            """
            INSERT INTO core.dim_organizacao (nome, tipo_organizacao, fonte_dado)
            VALUES (:nome, 'empresa', 'teste')
            RETURNING id_organizacao
            """
        ),
        {"nome": nome},
    ).first()
    return row[0]


def test_vw_intensidade_p_d_nao_estoura_com_faturamento_zero(db_conn):
    id_org = _criar_organizacao(db_conn)
    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_desempenho_organizacao
                (id_organizacao, id_tempo, faturamento, investimento_p_d, fonte_dado)
            VALUES (:id_organizacao, :id_tempo, 0, 1000, 'teste')
            """
        ),
        {"id_organizacao": id_org, "id_tempo": ID_TEMPO_EXEMPLO},
    )

    resultado = db_conn.execute(
        text("SELECT intensidade_p_d_pct FROM mart.vw_intensidade_p_d WHERE id_organizacao = :id_organizacao"),
        {"id_organizacao": id_org},
    ).first()

    assert resultado is not None
    assert resultado[0] is None  # NULLIF evita divisao por zero


def test_vw_produtividade_trabalhador_nao_estoura_com_zero_empregados(db_conn):
    id_org = _criar_organizacao(db_conn)
    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_desempenho_organizacao
                (id_organizacao, id_tempo, faturamento, numero_empregados, fonte_dado)
            VALUES (:id_organizacao, :id_tempo, 50000, 0, 'teste')
            """
        ),
        {"id_organizacao": id_org, "id_tempo": ID_TEMPO_EXEMPLO},
    )

    resultado = db_conn.execute(
        text(
            "SELECT produtividade_por_trabalhador FROM mart.vw_produtividade_trabalhador "
            "WHERE id_organizacao = :id_organizacao"
        ),
        {"id_organizacao": id_org},
    ).first()

    assert resultado is not None
    assert resultado[0] is None


def test_vw_taxa_primeira_inovacao_existe_e_vw_taxa_renovacao_antiga_nao_existe(db_conn):
    """Confere o rename: vw_taxa_renovacao_empresarial_inovadora (nome antigo,
    ambiguo) foi substituida por vw_taxa_primeira_inovacao."""
    db_conn.execute(text("SELECT * FROM mart.vw_taxa_primeira_inovacao"))  # nao deve lancar erro

    existe_view_antiga = db_conn.execute(
        text(
            "SELECT 1 FROM pg_views WHERE schemaname = 'mart' "
            "AND viewname = 'vw_taxa_renovacao_empresarial_inovadora'"
        )
    ).first()
    assert existe_view_antiga is None


def test_vw_conversao_conexoes_projetos_sem_conexoes_retorna_null_nao_erro(db_conn):
    db_conn.execute(text("DELETE FROM core.fato_conexao_ecossistema"))
    resultado = db_conn.execute(text("SELECT * FROM mart.vw_conversao_conexoes_projetos")).first()
    assert resultado is not None
    assert resultado.total_conexoes == 0
    assert resultado.taxa_conversao_pct is None


def test_vw_investimento_por_inovacao_sem_dados_retorna_null_nao_erro(db_conn):
    db_conn.execute(text("DELETE FROM core.fato_investimento_inovacao"))
    db_conn.execute(text("DELETE FROM core.fato_inovacao"))
    resultados = db_conn.execute(text("SELECT * FROM mart.vw_investimento_por_inovacao")).all()
    # sem linhas (nenhum ano) ou, se houver, sem exception de divisao por zero
    assert all(r.investimento_medio_por_inovacao is None or isinstance(r.investimento_medio_por_inovacao, (int, float)) for r in resultados)


def test_vw_conciliacao_investimento_pd_nao_estoura_com_autodeclarado_zero(db_conn):
    id_org = _criar_organizacao(db_conn, nome="Organizacao Conciliacao PD")
    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_desempenho_organizacao
                (id_organizacao, id_tempo, investimento_p_d, fonte_dado)
            VALUES (:id_organizacao, :id_tempo, 0, 'teste')
            """
        ),
        {"id_organizacao": id_org, "id_tempo": ID_TEMPO_EXEMPLO},
    )
    resultado = db_conn.execute(
        text(
            "SELECT diferenca_pct FROM mart.vw_conciliacao_investimento_pd "
            "WHERE id_organizacao = :id_organizacao"
        ),
        {"id_organizacao": id_org},
    ).first()
    assert resultado is not None
    assert resultado.diferenca_pct is None  # NULLIF evita divisao por zero


def test_vw_taxa_empresas_inovadoras_usa_respondentes_elegiveis_nao_todas_ativas(db_conn):
    """A organizacao so deve entrar no denominador se estiver em
    universo_pesquisado (elegivel) e cobertura_coleta (respondeu) do ano —
    nao basta estar ativa em core.dim_organizacao."""
    id_org_respondente = _criar_organizacao(db_conn, nome="Respondente Taxa Inovadoras")
    id_org_fora_do_universo = _criar_organizacao(db_conn, nome="Fora do Universo Pesquisado")

    id_ciclo = db_conn.execute(
        text(
            "INSERT INTO core.ciclo_coleta (nome, ano_referencia, fonte_dado) "
            "VALUES ('Ciclo Taxa Inovadoras', 2024, 'teste') RETURNING id_ciclo"
        )
    ).scalar_one()
    db_conn.execute(
        text(
            "INSERT INTO core.universo_pesquisado (id_ciclo, id_organizacao, elegivel, fonte_dado) "
            "VALUES (:id_ciclo, :id_organizacao, true, 'teste')"
        ),
        {"id_ciclo": id_ciclo, "id_organizacao": id_org_respondente},
    )
    db_conn.execute(
        text(
            "INSERT INTO core.cobertura_coleta (id_ciclo, id_organizacao, respondeu, fonte_dado) "
            "VALUES (:id_ciclo, :id_organizacao, true, 'teste')"
        ),
        {"id_ciclo": id_ciclo, "id_organizacao": id_org_respondente},
    )

    resultado = db_conn.execute(
        text("SELECT empresas_respondentes FROM mart.vw_taxa_empresas_inovadoras WHERE ano = 2024")
    ).first()
    assert resultado is not None
    assert resultado.empresas_respondentes == 1  # so o respondente elegivel, nao a org fora do universo
