"""Tela de importação: autorização (item 3/5 do pedido) e a role usada
para a carga (web_import — nunca a de administração, ver
db/roles/web_import.sql e etl/db.py::get_web_import_engine).
"""
from __future__ import annotations

import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from sqlalchemy import text

from etl.db import get_engine

pytestmark = pytest.mark.django_db

URL_IMPORTAR = "importacao:organizacoes"


def test_usuario_sem_permissao_recebe_403_no_get(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)
    resposta = client.get(reverse(URL_IMPORTAR))
    assert resposta.status_code == 403


def test_usuario_sem_permissao_recebe_403_no_post(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)
    csv = SimpleUploadedFile("orgs.csv", b"nome,tipo_organizacao\nX,empresa\n", content_type="text/csv")
    resposta = client.post(reverse(URL_IMPORTAR), {"arquivo": csv})
    assert resposta.status_code == 403


def test_usuario_do_grupo_importacao_acessa_a_tela(client, cria_usuario):
    usuario = cria_usuario("Importação")
    client.force_login(usuario)
    resposta = client.get(reverse(URL_IMPORTAR))
    assert resposta.status_code == 200


def test_importacao_nao_usa_a_role_de_administracao():
    """Guarda de regressão para o item 5 do pedido de revisão: a view não
    pode voltar a importar/usar etl.db.get_engine() (role POLO_DB_USER,
    privilégio total) dentro do processo web."""
    import importacao.views as views_importacao

    assert not hasattr(views_importacao, "get_engine")
    assert views_importacao.get_web_import_engine.__module__ == "etl.db"


def test_upload_autorizado_grava_organizacao_via_role_web_import(client, cria_usuario):
    usuario = cria_usuario("Importação")
    client.force_login(usuario)

    nome_org = f"Empresa Teste Import {uuid.uuid4().hex[:10]}"
    conteudo_csv = (
        "nome,tipo_organizacao,ativa,nome_contato,email_contato,telefone_contato,cargo_contato\n"
        f"{nome_org},empresa,true,Ciclano Teste,ciclano.teste@example.com,11999999999,Gerente\n"
    ).encode("utf-8")
    csv = SimpleUploadedFile("orgs.csv", conteudo_csv, content_type="text/csv")

    engine = get_engine()
    try:
        resposta = client.post(reverse(URL_IMPORTAR), {"arquivo": csv}, follow=True)
        assert resposta.status_code == 200
        mensagens = [str(m) for m in resposta.context["messages"]]
        assert any("1 inserido" in m for m in mensagens), mensagens

        with engine.connect() as conn:
            organizacao = conn.execute(
                text("SELECT id_organizacao FROM core.dim_organizacao WHERE nome = :nome"),
                {"nome": nome_org},
            ).first()
            assert organizacao is not None, "organização não foi gravada pela importação"
            id_organizacao = organizacao[0]

            contato = conn.execute(
                text("SELECT nome_contato, email FROM core.contato_organizacao WHERE id_organizacao = :id"),
                {"id": id_organizacao},
            ).first()
            assert contato is not None, "contato não foi gravado pela importação (role web_import sem INSERT em core?)"
            assert contato[0] == "Ciclano Teste"
            assert contato[1] == "ciclano.teste@example.com"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM core.contato_organizacao WHERE id_organizacao IN "
                    "(SELECT id_organizacao FROM core.dim_organizacao WHERE nome = :nome)"
                ),
                {"nome": nome_org},
            )
            id_execucoes = conn.execute(
                text("SELECT DISTINCT id_execucao FROM raw.organizacoes WHERE nome = :nome"),
                {"nome": nome_org},
            ).scalars().all()
            conn.execute(text("DELETE FROM core.dim_organizacao WHERE nome = :nome"), {"nome": nome_org})
            conn.execute(text("DELETE FROM raw.organizacoes WHERE nome = :nome"), {"nome": nome_org})
            for id_execucao in id_execucoes:
                conn.execute(
                    text("DELETE FROM etl.quarentena_registro WHERE id_execucao = :id"), {"id": id_execucao}
                )
                conn.execute(text("DELETE FROM etl.etl_execucao WHERE id_execucao = :id"), {"id": id_execucao})
