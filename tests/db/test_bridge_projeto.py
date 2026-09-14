"""Testes de core.bridge_projeto_organizacao / core.bridge_projeto_tecnologia:
dominio de papel, sincronizacao automatica com core.projeto (fonte de
verdade) e bloqueio de edicao direta divergente na bridge."""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def _criar_organizacao(conn, nome: str) -> int:
    return conn.execute(
        text(
            "INSERT INTO core.dim_organizacao (nome, tipo_organizacao, fonte_dado) "
            "VALUES (:nome, 'empresa', 'teste') RETURNING id_organizacao"
        ),
        {"nome": nome},
    ).scalar_one()


def _criar_projeto(conn, nome: str, id_organizacao_lider: int | None = None, id_tecnologia_principal: int | None = None) -> int:
    return conn.execute(
        text(
            """
            INSERT INTO core.projeto (nome, id_organizacao_lider, id_tecnologia_principal, fonte_dado)
            VALUES (:nome, :id_organizacao_lider, :id_tecnologia_principal, 'teste')
            RETURNING id_projeto
            """
        ),
        {
            "nome": nome,
            "id_organizacao_lider": id_organizacao_lider,
            "id_tecnologia_principal": id_tecnologia_principal,
        },
    ).scalar_one()


def _tecnologias(conn, n: int) -> list[int]:
    return conn.execute(text("SELECT id_tecnologia FROM core.dim_tecnologia LIMIT :n"), {"n": n}).scalars().all()


# --------------------------------------------------------------------- papel

def test_bridge_projeto_organizacao_rejeita_universidade_como_papel(db_conn):
    id_org = _criar_organizacao(db_conn, "Org Papel Universidade")
    id_projeto = _criar_projeto(db_conn, "Projeto Papel")
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    "INSERT INTO core.bridge_projeto_organizacao (id_projeto, id_organizacao, papel, fonte_dado) "
                    "VALUES (:id_projeto, :id_organizacao, 'universidade', 'teste')"
                ),
                {"id_projeto": id_projeto, "id_organizacao": id_org},
            )


def test_bridge_projeto_organizacao_rejeita_ict_como_papel(db_conn):
    id_org = _criar_organizacao(db_conn, "Org Papel ICT")
    id_projeto = _criar_projeto(db_conn, "Projeto Papel ICT")
    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    "INSERT INTO core.bridge_projeto_organizacao (id_projeto, id_organizacao, papel, fonte_dado) "
                    "VALUES (:id_projeto, :id_organizacao, 'ict', 'teste')"
                ),
                {"id_projeto": id_projeto, "id_organizacao": id_org},
            )


def test_bridge_projeto_organizacao_aceita_beneficiario(db_conn):
    id_org = _criar_organizacao(db_conn, "Org Beneficiaria")
    id_projeto = _criar_projeto(db_conn, "Projeto Beneficiario")
    db_conn.execute(
        text(
            "INSERT INTO core.bridge_projeto_organizacao (id_projeto, id_organizacao, papel, fonte_dado) "
            "VALUES (:id_projeto, :id_organizacao, 'beneficiario', 'teste')"
        ),
        {"id_projeto": id_projeto, "id_organizacao": id_org},
    )
    qtd = db_conn.execute(
        text(
            "SELECT count(*) FROM core.bridge_projeto_organizacao "
            "WHERE id_projeto = :id_projeto AND papel = 'beneficiario'"
        ),
        {"id_projeto": id_projeto},
    ).scalar_one()
    assert qtd == 1


# --------------------------------------------------------------- sync: lider

def test_projeto_sync_cria_linha_lider_na_bridge_ao_inserir(db_conn):
    id_org = _criar_organizacao(db_conn, "Org Lider Inicial")
    id_projeto = _criar_projeto(db_conn, "Projeto Com Lider", id_organizacao_lider=id_org)

    lideres = db_conn.execute(
        text("SELECT id_organizacao FROM core.bridge_projeto_organizacao WHERE id_projeto = :id_projeto AND papel = 'lider'"),
        {"id_projeto": id_projeto},
    ).scalars().all()
    assert lideres == [id_org]


def test_projeto_sync_atualiza_lider_ao_trocar_organizacao(db_conn):
    id_org_a = _criar_organizacao(db_conn, "Org Lider A")
    id_org_b = _criar_organizacao(db_conn, "Org Lider B")
    id_projeto = _criar_projeto(db_conn, "Projeto Troca Lider", id_organizacao_lider=id_org_a)

    db_conn.execute(
        text("UPDATE core.projeto SET id_organizacao_lider = :id_org_b WHERE id_projeto = :id_projeto"),
        {"id_org_b": id_org_b, "id_projeto": id_projeto},
    )

    lideres = db_conn.execute(
        text("SELECT id_organizacao FROM core.bridge_projeto_organizacao WHERE id_projeto = :id_projeto AND papel = 'lider'"),
        {"id_projeto": id_projeto},
    ).scalars().all()
    assert lideres == [id_org_b]


def test_projeto_sync_remove_lider_da_bridge_quando_setado_para_null(db_conn):
    id_org = _criar_organizacao(db_conn, "Org Lider Removido")
    id_projeto = _criar_projeto(db_conn, "Projeto Remove Lider", id_organizacao_lider=id_org)

    db_conn.execute(
        text("UPDATE core.projeto SET id_organizacao_lider = NULL WHERE id_projeto = :id_projeto"),
        {"id_projeto": id_projeto},
    )

    qtd = db_conn.execute(
        text("SELECT count(*) FROM core.bridge_projeto_organizacao WHERE id_projeto = :id_projeto AND papel = 'lider'"),
        {"id_projeto": id_projeto},
    ).scalar_one()
    assert qtd == 0


def test_projeto_sync_preserva_outros_papeis_do_ex_lider(db_conn):
    """Trocar o lider nao deve apagar outros papeis que a organizacao antiga
    ainda tenha no mesmo projeto (ex.: continua como parceira)."""
    id_org_a = _criar_organizacao(db_conn, "Org Lider Vira Parceira")
    id_org_b = _criar_organizacao(db_conn, "Org Nova Lider")
    id_projeto = _criar_projeto(db_conn, "Projeto Multi Papel", id_organizacao_lider=id_org_a)

    db_conn.execute(
        text(
            "INSERT INTO core.bridge_projeto_organizacao (id_projeto, id_organizacao, papel, fonte_dado) "
            "VALUES (:id_projeto, :id_org_a, 'parceiro', 'teste')"
        ),
        {"id_projeto": id_projeto, "id_org_a": id_org_a},
    )

    db_conn.execute(
        text("UPDATE core.projeto SET id_organizacao_lider = :id_org_b WHERE id_projeto = :id_projeto"),
        {"id_org_b": id_org_b, "id_projeto": id_projeto},
    )

    papeis_org_a = db_conn.execute(
        text(
            "SELECT papel FROM core.bridge_projeto_organizacao "
            "WHERE id_projeto = :id_projeto AND id_organizacao = :id_org_a"
        ),
        {"id_projeto": id_projeto, "id_org_a": id_org_a},
    ).scalars().all()
    assert papeis_org_a == ["parceiro"]  # 'lider' removido, 'parceiro' preservado


def test_bridge_projeto_organizacao_rejeita_insercao_direta_de_lider_divergente(db_conn):
    id_org_lider = _criar_organizacao(db_conn, "Org Lider Oficial")
    id_org_outra = _criar_organizacao(db_conn, "Org Outra Nao Lider")
    id_projeto = _criar_projeto(db_conn, "Projeto Guard Insert", id_organizacao_lider=id_org_lider)

    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    "INSERT INTO core.bridge_projeto_organizacao (id_projeto, id_organizacao, papel, fonte_dado) "
                    "VALUES (:id_projeto, :id_org_outra, 'lider', 'teste')"
                ),
                {"id_projeto": id_projeto, "id_org_outra": id_org_outra},
            )


def test_bridge_projeto_organizacao_rejeita_delete_direto_do_lider_atual(db_conn):
    id_org = _criar_organizacao(db_conn, "Org Lider Protegida")
    id_projeto = _criar_projeto(db_conn, "Projeto Guard Delete", id_organizacao_lider=id_org)

    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    "DELETE FROM core.bridge_projeto_organizacao "
                    "WHERE id_projeto = :id_projeto AND papel = 'lider'"
                ),
                {"id_projeto": id_projeto},
            )


# --------------------------------------------------------- sync: tecnologia

def test_projeto_sync_cria_e_atualiza_tecnologia_principal(db_conn):
    tec_a, tec_b = _tecnologias(db_conn, 2)
    id_projeto = _criar_projeto(db_conn, "Projeto Tecnologia", id_tecnologia_principal=tec_a)

    principal = db_conn.execute(
        text(
            "SELECT id_tecnologia FROM core.bridge_projeto_tecnologia "
            "WHERE id_projeto = :id_projeto AND principal"
        ),
        {"id_projeto": id_projeto},
    ).scalar_one()
    assert principal == tec_a

    db_conn.execute(
        text("UPDATE core.projeto SET id_tecnologia_principal = :tec_b WHERE id_projeto = :id_projeto"),
        {"tec_b": tec_b, "id_projeto": id_projeto},
    )

    principal_depois = db_conn.execute(
        text(
            "SELECT id_tecnologia FROM core.bridge_projeto_tecnologia "
            "WHERE id_projeto = :id_projeto AND principal"
        ),
        {"id_projeto": id_projeto},
    ).scalar_one()
    assert principal_depois == tec_b

    ainda_marcada = db_conn.execute(
        text(
            "SELECT principal FROM core.bridge_projeto_tecnologia "
            "WHERE id_projeto = :id_projeto AND id_tecnologia = :tec_a"
        ),
        {"id_projeto": id_projeto, "tec_a": tec_a},
    ).scalar_one()
    assert ainda_marcada is False  # tecnologia antiga continua na bridge, so deixa de ser "principal"


def test_bridge_projeto_tecnologia_rejeita_principal_divergente(db_conn):
    tec_a, tec_b = _tecnologias(db_conn, 2)
    id_projeto = _criar_projeto(db_conn, "Projeto Guard Tecnologia", id_tecnologia_principal=tec_a)

    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    "INSERT INTO core.bridge_projeto_tecnologia (id_projeto, id_tecnologia, principal) "
                    "VALUES (:id_projeto, :tec_b, true)"
                ),
                {"id_projeto": id_projeto, "tec_b": tec_b},
            )


def test_bridge_projeto_tecnologia_rejeita_delete_direto_da_principal_atual(db_conn):
    tec_a, = _tecnologias(db_conn, 1)
    id_projeto = _criar_projeto(db_conn, "Projeto Guard Delete Tecnologia", id_tecnologia_principal=tec_a)

    with pytest.raises(IntegrityError):
        with db_conn.begin_nested():
            db_conn.execute(
                text(
                    "DELETE FROM core.bridge_projeto_tecnologia "
                    "WHERE id_projeto = :id_projeto AND id_tecnologia = :tec_a"
                ),
                {"id_projeto": id_projeto, "tec_a": tec_a},
            )


# --------------------------------------------------------------- cascata

def test_projeto_delete_cascata_nao_e_bloqueado_pelo_guard(db_conn):
    id_org = _criar_organizacao(db_conn, "Org Projeto Deletado")
    tec_a, = _tecnologias(db_conn, 1)
    id_projeto = _criar_projeto(
        db_conn, "Projeto Para Deletar", id_organizacao_lider=id_org, id_tecnologia_principal=tec_a
    )

    db_conn.execute(text("DELETE FROM core.projeto WHERE id_projeto = :id_projeto"), {"id_projeto": id_projeto})

    restam_org = db_conn.execute(
        text("SELECT count(*) FROM core.bridge_projeto_organizacao WHERE id_projeto = :id_projeto"),
        {"id_projeto": id_projeto},
    ).scalar_one()
    restam_tec = db_conn.execute(
        text("SELECT count(*) FROM core.bridge_projeto_tecnologia WHERE id_projeto = :id_projeto"),
        {"id_projeto": id_projeto},
    ).scalar_one()
    assert restam_org == 0
    assert restam_tec == 0
