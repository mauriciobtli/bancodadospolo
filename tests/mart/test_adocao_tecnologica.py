"""mart.vw_adocao_tecnologia deve preservar o historico de cada ciclo de
coleta — o estado 'mais recente' e calculado DENTRO de cada ciclo
(id_ciclo + organizacao + tecnologia), nao colapsado entre ciclos."""
from __future__ import annotations

from sqlalchemy import text


def _criar_organizacao(conn, nome: str) -> int:
    return conn.execute(
        text(
            "INSERT INTO core.dim_organizacao (nome, tipo_organizacao, fonte_dado) "
            "VALUES (:nome, 'empresa', 'teste') RETURNING id_organizacao"
        ),
        {"nome": nome},
    ).scalar_one()


def _criar_ciclo_com_cobertura(conn, nome: str, ano: int, id_organizacao: int) -> int:
    id_ciclo = conn.execute(
        text(
            "INSERT INTO core.ciclo_coleta (nome, ano_referencia, fonte_dado) "
            "VALUES (:nome, :ano, 'teste') RETURNING id_ciclo"
        ),
        {"nome": nome, "ano": ano},
    ).scalar_one()
    conn.execute(
        text(
            "INSERT INTO core.universo_pesquisado (id_ciclo, id_organizacao, elegivel, fonte_dado) "
            "VALUES (:id_ciclo, :id_organizacao, true, 'teste')"
        ),
        {"id_ciclo": id_ciclo, "id_organizacao": id_organizacao},
    )
    conn.execute(
        text(
            "INSERT INTO core.cobertura_coleta (id_ciclo, id_organizacao, respondeu, fonte_dado) "
            "VALUES (:id_ciclo, :id_organizacao, true, 'teste')"
        ),
        {"id_ciclo": id_ciclo, "id_organizacao": id_organizacao},
    )
    return id_ciclo


def test_vw_adocao_tecnologia_preserva_historico_de_dois_ciclos(db_conn):
    id_org = _criar_organizacao(db_conn, "Organizacao Dois Ciclos")
    id_tecnologia = db_conn.execute(text("SELECT id_tecnologia FROM core.dim_tecnologia LIMIT 1")).scalar_one()

    id_ciclo_2023 = _criar_ciclo_com_cobertura(db_conn, "Ciclo 2023", 2023, id_org)
    id_ciclo_2024 = _criar_ciclo_com_cobertura(db_conn, "Ciclo 2024", 2024, id_org)

    # id_tempo diferentes (dois anos distintos), nivel de adocao evoluiu de 1 para 3.
    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_adocao_tecnologica
                (id_organizacao, id_tecnologia, id_tempo, id_ciclo, nivel_adocao, fonte_dado)
            VALUES
                (:id_organizacao, :id_tecnologia, 20230601, :id_ciclo_2023, 1, 'teste'),
                (:id_organizacao, :id_tecnologia, 20240601, :id_ciclo_2024, 3, 'teste')
            """
        ),
        {
            "id_organizacao": id_org,
            "id_tecnologia": id_tecnologia,
            "id_ciclo_2023": id_ciclo_2023,
            "id_ciclo_2024": id_ciclo_2024,
        },
    )

    linhas = db_conn.execute(
        text(
            "SELECT id_ciclo, ano, nivel_adocao, qtd_organizacoes FROM mart.vw_adocao_tecnologia "
            "WHERE id_tecnologia = :id_tecnologia ORDER BY ano"
        ),
        {"id_tecnologia": id_tecnologia},
    ).all()

    assert len(linhas) == 2, "os dois ciclos devem permanecer consultaveis, nao apenas o mais recente"
    linha_2023, linha_2024 = linhas
    assert linha_2023.id_ciclo == id_ciclo_2023
    assert linha_2023.ano == 2023
    assert linha_2023.nivel_adocao == 1
    assert linha_2023.qtd_organizacoes == 1

    assert linha_2024.id_ciclo == id_ciclo_2024
    assert linha_2024.ano == 2024
    assert linha_2024.nivel_adocao == 3
    assert linha_2024.qtd_organizacoes == 1


def test_vw_adocao_tecnologia_pega_estado_mais_recente_dentro_do_mesmo_ciclo(db_conn):
    """Dentro de UM MESMO ciclo, se houver mais de uma medicao (id_tempo
    diferentes) para a mesma organizacao+tecnologia, so a mais recente conta."""
    id_org = _criar_organizacao(db_conn, "Organizacao Mesmo Ciclo")
    id_tecnologia = db_conn.execute(text("SELECT id_tecnologia FROM core.dim_tecnologia LIMIT 1")).scalar_one()
    id_ciclo = _criar_ciclo_com_cobertura(db_conn, "Ciclo Unico", 2024, id_org)

    db_conn.execute(
        text(
            """
            INSERT INTO core.fato_adocao_tecnologica
                (id_organizacao, id_tecnologia, id_tempo, id_ciclo, nivel_adocao, fonte_dado)
            VALUES
                (:id_organizacao, :id_tecnologia, 20240101, :id_ciclo, 1, 'teste'),
                (:id_organizacao, :id_tecnologia, 20240601, :id_ciclo, 2, 'teste')
            """
        ),
        {"id_organizacao": id_org, "id_tecnologia": id_tecnologia, "id_ciclo": id_ciclo},
    )

    linhas = db_conn.execute(
        text(
            "SELECT nivel_adocao FROM mart.vw_adocao_tecnologia "
            "WHERE id_ciclo = :id_ciclo AND id_tecnologia = :id_tecnologia"
        ),
        {"id_ciclo": id_ciclo, "id_tecnologia": id_tecnologia},
    ).all()

    assert len(linhas) == 1
    assert linhas[0].nivel_adocao == 2
