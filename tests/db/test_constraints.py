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
