"""Campo "Ano de referência" (AnoParaTempoFormField, ver
core_admin/admin/mixins.py) em criação e edição — item 6 do pedido de
revisão: ao reabrir um registro cujo id_tempo é 20241231, o formulário
deve mostrar 2024, nunca o inteiro bruto. Testa o ciclo completo pedido
explicitamente: criar, reabrir, editar e salvar.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from core_admin.models.desempenho import DesempenhoOrganizacao
from core_admin.models.organizacoes import Organizacao

pytestmark = pytest.mark.django_db

CNPJ_VALIDO = "11122233000183"


@pytest.fixture
def organizacao(db) -> Organizacao:
    return Organizacao.objects.create(nome="Organização Teste Ano Referência", cnpj=CNPJ_VALIDO, tipo_organizacao="empresa")


def _dados_formulario(organizacao: Organizacao, ano: int, faturamento: str) -> dict:
    return {
        "organizacao": organizacao.pk,
        "tempo": str(ano),
        "faturamento": faturamento,
        "fonte_dado": "admin_web",
    }


def test_criar_reabrir_editar_e_salvar(client, cria_usuario, organizacao):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)

    url_add = reverse("admin:core_admin_desempenhoorganizacao_add")
    resposta = client.post(url_add, _dados_formulario(organizacao, 2024, "1000.00"), follow=True)
    assert resposta.status_code == 200

    registro = DesempenhoOrganizacao.objects.get(organizacao=organizacao)
    assert registro.tempo_id == 20241231, "criação não resolveu o ano 2024 para 31/12/2024 em dim_tempo"
    assert registro.faturamento == Decimal("1000.00")

    url_change = reverse("admin:core_admin_desempenhoorganizacao_change", args=[registro.pk])
    resposta_get = client.get(url_change)
    assert resposta_get.status_code == 200
    corpo = resposta_get.content.decode()
    assert 'name="tempo"' in corpo
    assert 'value="2024"' in corpo, "reabrir o registro deveria mostrar o ano (2024), não o id_tempo bruto"
    assert "20241231" not in corpo, "id_tempo bruto (20241231) vazou para a tela em vez do ano"

    resposta_post = client.post(url_change, _dados_formulario(organizacao, 2024, "2500.50"), follow=True)
    assert resposta_post.status_code == 200

    registro.refresh_from_db()
    assert registro.tempo_id == 20241231, "edição não deveria alterar o id_tempo para um ano igual"
    assert registro.faturamento == Decimal("2500.50")

    resposta_get_2 = client.get(url_change)
    assert 'value="2024"' in resposta_get_2.content.decode()


def test_editar_trocando_o_ano(client, cria_usuario, organizacao):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)

    url_add = reverse("admin:core_admin_desempenhoorganizacao_add")
    client.post(url_add, _dados_formulario(organizacao, 2020, "10.00"), follow=True)
    registro = DesempenhoOrganizacao.objects.get(organizacao=organizacao)
    assert registro.tempo_id == 20201231

    url_change = reverse("admin:core_admin_desempenhoorganizacao_change", args=[registro.pk])
    client.post(url_change, _dados_formulario(organizacao, 2021, "20.00"), follow=True)

    registro.refresh_from_db()
    assert registro.tempo_id == 20211231


def test_ano_fora_do_calendario_disponivel_e_rejeitado(client, cria_usuario, organizacao):
    usuario = cria_usuario("Cadastro")
    client.force_login(usuario)

    url_add = reverse("admin:core_admin_desempenhoorganizacao_add")
    resposta = client.post(url_add, _dados_formulario(organizacao, 1999, "10.00"))
    assert resposta.status_code == 200
    assert not DesempenhoOrganizacao.objects.filter(organizacao=organizacao).exists()
