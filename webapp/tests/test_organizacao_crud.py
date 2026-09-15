"""CRUD de Organização pelo admin web (grupo Cadastro), incluindo a
validação de CNPJ reaproveitada de etl.validators.cnpj (não duplicada)."""
from __future__ import annotations

import pytest
from django.urls import reverse

from core_admin.models.organizacoes import Organizacao

pytestmark = pytest.mark.django_db

CNPJ_VALIDO_1 = "11122233000183"
CNPJ_VALIDO_2 = "22233344000183"


def _dados(nome: str, cnpj: str = "") -> dict:
    return {
        "nome": nome,
        "nome_fantasia": "",
        "cnpj": cnpj,
        "tipo_organizacao": "empresa",
        "site": "",
        "municipio": "",
        "setor": "",
        "porte": "nao_informado",
        "ano_fundacao": "",
        "ativa": "on",
        "data_entrada_ecossistema": "",
        "data_saida_ecossistema": "",
        "motivo_saida": "",
        "fonte_dado": "admin_web",
        "data_coleta": "",
        "contatos-TOTAL_FORMS": "0",
        "contatos-INITIAL_FORMS": "0",
        "contatos-MIN_NUM_FORMS": "0",
        "contatos-MAX_NUM_FORMS": "1000",
    }


def test_criar_organizacao(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)

    url_add = reverse("admin:core_admin_organizacao_add")
    resposta = client.post(url_add, _dados("Organização CRUD Teste", CNPJ_VALIDO_1), follow=True)
    assert resposta.status_code == 200

    organizacao = Organizacao.objects.get(nome="Organização CRUD Teste")
    assert organizacao.cnpj == CNPJ_VALIDO_1
    assert organizacao.tipo_organizacao == "empresa"


def test_cnpj_invalido_e_rejeitado(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)

    url_add = reverse("admin:core_admin_organizacao_add")
    resposta = client.post(url_add, _dados("Organização CNPJ Inválido", "11122233000184"))
    assert resposta.status_code == 200
    assert not Organizacao.objects.filter(nome="Organização CNPJ Inválido").exists()


def test_listar_e_buscar_organizacao(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)
    organizacao = Organizacao.objects.create(nome="Organização Busca Teste", tipo_organizacao="startup")

    url_lista = reverse("admin:core_admin_organizacao_changelist")
    resposta = client.get(url_lista, {"q": "Organização Busca Teste"})
    assert resposta.status_code == 200
    assert organizacao.nome in resposta.content.decode()


def test_editar_organizacao(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)
    organizacao = Organizacao.objects.create(nome="Organização Editar Teste", tipo_organizacao="empresa")

    url_change = reverse("admin:core_admin_organizacao_change", args=[organizacao.pk])
    resposta = client.post(url_change, _dados("Organização Editar Teste (renomeada)", ""), follow=True)
    assert resposta.status_code == 200

    organizacao.refresh_from_db()
    assert organizacao.nome == "Organização Editar Teste (renomeada)"


def test_apagar_organizacao(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)
    organizacao = Organizacao.objects.create(nome="Organização Apagar Teste", tipo_organizacao="empresa")

    url_delete = reverse("admin:core_admin_organizacao_delete", args=[organizacao.pk])
    resposta = client.post(url_delete, {"post": "yes"}, follow=True)
    assert resposta.status_code == 200
    assert not Organizacao.objects.filter(pk=organizacao.pk).exists()


def test_usuario_leitura_nao_pode_criar_organizacao(client, cria_usuario):
    usuario = cria_usuario("Leitura")
    client.force_login(usuario)

    url_add = reverse("admin:core_admin_organizacao_add")
    resposta = client.get(url_add)
    assert resposta.status_code == 403


def test_usuario_cadastro_nao_ve_aba_de_contatos(client, cria_usuario):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)
    organizacao = Organizacao.objects.create(nome="Organização Sem Contato Visível", tipo_organizacao="empresa")

    url_change = reverse("admin:core_admin_organizacao_change", args=[organizacao.pk])
    resposta = client.get(url_change)
    assert resposta.status_code == 200
    assert "contatos-TOTAL_FORMS" not in resposta.content.decode()
