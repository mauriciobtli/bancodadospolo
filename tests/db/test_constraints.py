"""Testes de integridade do schema core: PK/FK, duplicidade, dominios,
valores negativos e datas inconsistentes. Requer Postgres com as
migrations aplicadas (ver tests/conftest.py).

Cada asserção de erro roda dentro de um SAVEPOINT (begin_nested): quando o
INSERT falha, so o savepoint e desfeito, mantendo a transacao externa do
teste (aberta pela fixture db_conn) utilizavel para os proximos comandos.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

ID_TEMPO_EXEMPLO = 20220101


def _criar_organizacao(conn, nome: str = "Organizacao Teste", cnpj: str | None = None) -> int:
    row = conn.execute(
        text(
            """
            INSERT INTO core.dim_organizacao (nome, cnpj, tipo_organizacao, fonte_dado)
            VALUES (:nome, :cnpj, 'empresa', 'teste')
            RETURNING id_organizacao
            """
        ),
        {"nome": nome, "cnpj": cnpj},
    ).first()
    return row[0]


def test_fato_inovacao_rejeita_organizacao_inexistente(db_conn):
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.fato_inovacao
                        (id_organizacao, nome, id_tipo_inovacao, id_grau_novidade, fonte_dado)
                    VALUES (999999999, 'Inovacao X',
                            (SELECT id_tipo_inovacao FROM core.dim_tipo_inovacao LIMIT 1),
                            (SELECT id_grau_novidade FROM core.dim_grau_novidade LIMIT 1),
                            'teste')
                    """
                )
            )


def test_fato_desempenho_organizacao_rejeita_duplicidade_de_grao(db_conn):
    id_org = _criar_organizacao(db_conn)
    params = {"id_organizacao": id_org, "id_tempo": ID_TEMPO_EXEMPLO}
    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_desempenho_organizacao (id_organizacao, id_tempo, fonte_dado)
            VALUES (:id_organizacao, :id_tempo, 'teste')
            """
        ),
        params,
    )
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.fato_desempenho_organizacao (id_organizacao, id_tempo, fonte_dado)
                    VALUES (:id_organizacao, :id_tempo, 'teste')
                    """
                ),
                params,
            )


def test_dim_organizacao_rejeita_cnpj_com_letras(db_conn):
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            _criar_organizacao(db_conn, cnpj="ABCDEFGHIJKLMN")


def test_dim_organizacao_rejeita_tipo_fora_do_dominio(db_conn):
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.dim_organizacao (nome, tipo_organizacao, fonte_dado)
                    VALUES ('Organizacao Invalida', 'tipo_que_nao_existe', 'teste')
                    """
                )
            )


def test_fato_desempenho_organizacao_rejeita_faturamento_negativo(db_conn):
    id_org = _criar_organizacao(db_conn)
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.fato_desempenho_organizacao
                        (id_organizacao, id_tempo, faturamento, fonte_dado)
                    VALUES (:id_organizacao, :id_tempo, -100, 'teste')
                    """
                ),
                {"id_organizacao": id_org, "id_tempo": ID_TEMPO_EXEMPLO},
            )


def test_projeto_rejeita_data_fim_prevista_antes_do_inicio(db_conn):
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.projeto (nome, data_inicio, data_fim_prevista, fonte_dado)
                    VALUES ('Projeto Invalido', '2024-06-01', '2024-01-01', 'teste')
                    """
                )
            )


def test_fato_conexao_ecossistema_rejeita_origem_igual_destino(db_conn):
    id_org = _criar_organizacao(db_conn)
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.fato_conexao_ecossistema
                        (id_organizacao_origem, id_organizacao_destino, tipo_conexao, fonte_dado)
                    VALUES (:id_org, :id_org, 'parceria', 'teste')
                    """
                ),
                {"id_org": id_org},
            )


def test_fato_investimento_rejeita_duplicidade_com_id_projeto_nulo(db_conn):
    """UNIQUE NULLS NOT DISTINCT: duas linhas com o mesmo grao e AMBAS sem
    id_projeto devem ser tratadas como duplicata, nao como registros distintos."""
    id_org = _criar_organizacao(db_conn)
    id_fonte = db_conn.execute(text("SELECT id_fonte_recurso FROM core.dim_fonte_recurso LIMIT 1")).scalar_one()
    params = {
        "id_organizacao": id_org,
        "id_tempo": ID_TEMPO_EXEMPLO,
        "id_fonte_recurso": id_fonte,
    }
    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_investimento_inovacao
                (id_organizacao, id_tempo, id_fonte_recurso, categoria, valor, fonte_dado)
            VALUES (:id_organizacao, :id_tempo, :id_fonte_recurso, 'p_d', 1000, 'teste')
            """
        ),
        params,
    )
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.fato_investimento_inovacao
                        (id_organizacao, id_tempo, id_fonte_recurso, categoria, valor, fonte_dado)
                    VALUES (:id_organizacao, :id_tempo, :id_fonte_recurso, 'p_d', 2000, 'teste')
                    """
                ),
                params,
            )


def test_bridge_projeto_organizacao_rejeita_papel_fora_do_dominio(db_conn):
    id_org = _criar_organizacao(db_conn)
    id_projeto = db_conn.execute(
        text("INSERT INTO core.projeto (nome, fonte_dado) VALUES ('Projeto Teste', 'teste') RETURNING id_projeto")
    ).scalar_one()
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.bridge_projeto_organizacao (id_projeto, id_organizacao, papel, fonte_dado)
                    VALUES (:id_projeto, :id_organizacao, 'papel_inexistente', 'teste')
                    """
                ),
                {"id_projeto": id_projeto, "id_organizacao": id_org},
            )


def test_bridge_projeto_tecnologia_rejeita_mais_de_uma_principal(db_conn):
    id_projeto = db_conn.execute(
        text("INSERT INTO core.projeto (nome, fonte_dado) VALUES ('Projeto Teste', 'teste') RETURNING id_projeto")
    ).scalar_one()
    tecnologias = db_conn.execute(text("SELECT id_tecnologia FROM core.dim_tecnologia LIMIT 2")).scalars().all()
    db_conn.execute(
        text(
            """
            INSERT INTO core.bridge_projeto_tecnologia (id_projeto, id_tecnologia, principal)
            VALUES (:id_projeto, :id_tecnologia, true)
            """
        ),
        {"id_projeto": id_projeto, "id_tecnologia": tecnologias[0]},
    )
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.bridge_projeto_tecnologia (id_projeto, id_tecnologia, principal)
                    VALUES (:id_projeto, :id_tecnologia, true)
                    """
                ),
                {"id_projeto": id_projeto, "id_tecnologia": tecnologias[1]},
            )


def test_dim_organizacao_rejeita_data_saida_antes_da_entrada(db_conn):
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    """
                    INSERT INTO core.dim_organizacao
                        (nome, tipo_organizacao, data_entrada_ecossistema, data_saida_ecossistema, fonte_dado)
                    VALUES ('Organizacao Invalida', 'empresa', '2024-06-01', '2024-01-01', 'teste')
                    """
                )
            )


def test_cobertura_coleta_distingue_nao_respondente_de_declarou_nao_utilizar(db_conn):
    """Base do requisito: distinguir organizacao nao-respondente de
    organizacao que respondeu e declarou nao utilizar uma tecnologia."""
    id_org_respondente = _criar_organizacao(db_conn, nome="Respondente Declarou Nao Uso")
    id_org_nao_respondente = _criar_organizacao(db_conn, nome="Nao Respondente")

    id_ciclo = db_conn.execute(
        text(
            """
            INSERT INTO core.ciclo_coleta (nome, ano_referencia, fonte_dado)
            VALUES ('Ciclo Teste', 2024, 'teste')
            RETURNING id_ciclo
            """
        )
    ).scalar_one()

    for id_org in (id_org_respondente, id_org_nao_respondente):
        db_conn.execute(
            text(
                """
                INSERT INTO core.universo_pesquisado (id_ciclo, id_organizacao, elegivel, fonte_dado)
                VALUES (:id_ciclo, :id_organizacao, true, 'teste')
                """
            ),
            {"id_ciclo": id_ciclo, "id_organizacao": id_org},
        )

    db_conn.execute(
        text(
            """
            INSERT INTO core.cobertura_coleta (id_ciclo, id_organizacao, respondeu, fonte_dado)
            VALUES (:id_ciclo, :id_org_respondeu, true, 'teste'),
                   (:id_ciclo, :id_org_nao_respondeu, false, 'teste')
            """
        ),
        {"id_ciclo": id_ciclo, "id_org_respondeu": id_org_respondente, "id_org_nao_respondeu": id_org_nao_respondente},
    )

    id_tecnologia = db_conn.execute(text("SELECT id_tecnologia FROM core.dim_tecnologia LIMIT 1")).scalar_one()
    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_adocao_tecnologica
                (id_organizacao, id_tecnologia, id_tempo, id_ciclo, nivel_adocao, fonte_dado)
            VALUES (:id_organizacao, :id_tecnologia, :id_tempo, :id_ciclo, 0, 'teste')
            """
        ),
        {
            "id_organizacao": id_org_respondente,
            "id_tecnologia": id_tecnologia,
            "id_tempo": ID_TEMPO_EXEMPLO,
            "id_ciclo": id_ciclo,
        },
    )

    respondentes = db_conn.execute(
        text("SELECT id_organizacao FROM mart.vw_respondentes_elegiveis WHERE id_ciclo = :id_ciclo"),
        {"id_ciclo": id_ciclo},
    ).scalars().all()
    assert id_org_respondente in respondentes
    assert id_org_nao_respondente not in respondentes

    adocao = db_conn.execute(
        text(
            "SELECT nivel_adocao, qtd_organizacoes, total_respondentes FROM mart.vw_adocao_tecnologia "
            "WHERE id_ciclo = :id_ciclo AND id_tecnologia = :id_tecnologia"
        ),
        {"id_ciclo": id_ciclo, "id_tecnologia": id_tecnologia},
    ).first()
    assert adocao is not None
    assert adocao.nivel_adocao == 0
    assert adocao.qtd_organizacoes == 1  # so o respondente que DECLAROU nao usar
    assert adocao.total_respondentes == 1  # nao-respondente nao entra no denominador
