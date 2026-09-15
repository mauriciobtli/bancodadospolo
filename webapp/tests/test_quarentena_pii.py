"""Proteção de PII na quarentena (item 4 do pedido de revisão de
segurança/LGPD): dados_originais pode conter nome/e-mail/telefone/cargo
de contato (colunas de contato da importação de organizações) — usuários
sem a permissão nativa sobre ContatoOrganizacao (grupo "Contatos") não
podem ver esses valores, nem na tela de detalhe da quarentena.

As linhas de etl.etl_execucao/etl.quarentena_registro são inseridas aqui
por uma conexão separada (etl.db.get_engine(), a role de administração
real usada pelo ETL) porque django_app só tem SELECT em etl (ver
db/roles/django_app.sql) — o mesmo caminho de escrita real de produção,
onde quem grava ali é sempre o pipeline de ETL, nunca o Django
diretamente. Por rodar numa conexão separada da transação de teste do
Django (que só cobre o alias "default"), a limpeza é manual.
"""
from __future__ import annotations

import json

import pytest
from django.urls import reverse
from sqlalchemy import text

from core_admin.admin.importacao_historico import MASCARA
from etl.db import get_engine

pytestmark = pytest.mark.django_db

DADOS_ORIGINAIS = {
    "nome": "Organização Teste PII",
    "cnpj": None,
    "nome_contato": "Fulano da Silva Teste",
    "email_contato": "fulano.teste.pii@example.com",
    "telefone_contato": "(11) 90000-0000",
    "cargo_contato": "Diretor de Teste",
}


@pytest.fixture
def registro_em_quarentena():
    engine = get_engine()
    with engine.begin() as conn:
        id_execucao = conn.execute(
            text(
                "INSERT INTO etl.etl_execucao (arquivo_fonte, tipo_fonte, entidade_alvo, status) "
                "VALUES ('teste_pii.csv', 'csv', 'core.dim_organizacao', 'sucesso_parcial') "
                "RETURNING id_execucao"
            )
        ).scalar_one()
        id_quarentena = conn.execute(
            text(
                "INSERT INTO etl.quarentena_registro "
                "(id_execucao, entidade, linha_origem, dados_originais, motivo_rejeicao, resolvido) "
                "VALUES (:id_execucao, 'organizacao', 1, CAST(:dados AS jsonb), 'cnpj_invalido', false) "
                "RETURNING id_quarentena"
            ),
            {"id_execucao": id_execucao, "dados": json.dumps(DADOS_ORIGINAIS, ensure_ascii=False)},
        ).scalar_one()
    yield id_quarentena
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM etl.quarentena_registro WHERE id_quarentena = :id"), {"id": id_quarentena})
        conn.execute(text("DELETE FROM etl.etl_execucao WHERE id_execucao = :id"), {"id": id_execucao})


def test_cadastro_nao_ve_pii_mas_ve_o_resto(client, cria_usuario, registro_em_quarentena):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)
    url = reverse("admin:core_admin_quarentenaregistro_change", args=[registro_em_quarentena])
    resposta = client.get(url)
    assert resposta.status_code == 200
    corpo = resposta.content.decode()
    assert "Fulano da Silva Teste" not in corpo
    assert "fulano.teste.pii@example.com" not in corpo
    assert "(11) 90000-0000" not in corpo
    assert "Diretor de Teste" not in corpo
    assert MASCARA in corpo
    assert "cnpj_invalido" in corpo


def test_leitura_nao_ve_pii(client, cria_usuario, registro_em_quarentena):
    usuario = cria_usuario("Leitura")
    client.force_login(usuario)
    url = reverse("admin:core_admin_quarentenaregistro_change", args=[registro_em_quarentena])
    resposta = client.get(url)
    assert resposta.status_code == 200
    corpo = resposta.content.decode()
    assert "fulano.teste.pii@example.com" not in corpo
    assert MASCARA in corpo


def test_contatos_ve_pii_sem_mascara(client, cria_usuario, registro_em_quarentena):
    usuario = cria_usuario("Contatos")
    client.force_login(usuario)
    url = reverse("admin:core_admin_quarentenaregistro_change", args=[registro_em_quarentena])
    resposta = client.get(url)
    assert resposta.status_code == 200
    corpo = resposta.content.decode()
    assert "Fulano da Silva Teste" in corpo
    assert "fulano.teste.pii@example.com" in corpo


def test_superusuario_ve_pii_sem_mascara(client, cria_usuario, registro_em_quarentena):
    usuario = cria_usuario(superuser=True)
    client.force_login(usuario)
    url = reverse("admin:core_admin_quarentenaregistro_change", args=[registro_em_quarentena])
    resposta = client.get(url)
    assert resposta.status_code == 200
    assert "fulano.teste.pii@example.com" in resposta.content.decode()


def test_usuario_sem_permissao_nenhuma_recebe_403(client, cria_usuario, registro_em_quarentena):
    usuario = cria_usuario()
    client.force_login(usuario)
    url = reverse("admin:core_admin_quarentenaregistro_change", args=[registro_em_quarentena])
    resposta = client.get(url)
    assert resposta.status_code == 403
