"""Ciclos de coleta com PK composta (UniversoPesquisado/CoberturaColeta
usam django.db.models.CompositePrimaryKey — não têm tela própria no
admin, só existem como aba do ciclo, ver webapp/README.md) e a FK composta
cobertura_coleta -> universo_pesquisado (uma organização só pode ter
cobertura registrada num ciclo se já estiver no universo pesquisado
daquele mesmo ciclo)."""
from __future__ import annotations

import pytest
from django.db import IntegrityError

from core_admin.models.organizacoes import Organizacao
from core_admin.models.pesquisa import CicloColeta, CoberturaColeta, UniversoPesquisado

pytestmark = pytest.mark.django_db


@pytest.fixture
def ciclo(db) -> CicloColeta:
    return CicloColeta.objects.create(nome="Ciclo Teste 2024", ano_referencia=2024)


@pytest.fixture
def organizacao(db) -> Organizacao:
    return Organizacao.objects.create(nome="Organização Ciclo Teste", tipo_organizacao="empresa")


def test_criar_universo_pesquisado_com_pk_composta(ciclo, organizacao):
    universo = UniversoPesquisado.objects.create(ciclo=ciclo, organizacao=organizacao)
    assert universo.pk == (ciclo.pk, organizacao.pk)
    assert UniversoPesquisado.objects.filter(ciclo=ciclo, organizacao=organizacao).exists()


def test_criar_cobertura_para_organizacao_no_universo(ciclo, organizacao):
    UniversoPesquisado.objects.create(ciclo=ciclo, organizacao=organizacao)
    cobertura = CoberturaColeta.objects.create(ciclo=ciclo, organizacao=organizacao, respondeu=True)
    assert cobertura.pk == (ciclo.pk, organizacao.pk)


def test_cobertura_sem_organizacao_no_universo_e_rejeitada(ciclo, organizacao):
    """FK composta (ciclo_coleta, organizacao) -> universo_pesquisado: não
    se pode registrar cobertura para quem não está no universo pesquisado
    do mesmo ciclo (ver db/schemas/24_core_cobertura.sql)."""
    with pytest.raises(IntegrityError):
        CoberturaColeta.objects.create(ciclo=ciclo, organizacao=organizacao, respondeu=True)


def test_dois_ciclos_podem_ter_a_mesma_organizacao_no_universo(organizacao):
    ciclo_1 = CicloColeta.objects.create(nome="Ciclo Teste A", ano_referencia=2023)
    ciclo_2 = CicloColeta.objects.create(nome="Ciclo Teste B", ano_referencia=2024)
    UniversoPesquisado.objects.create(ciclo=ciclo_1, organizacao=organizacao)
    UniversoPesquisado.objects.create(ciclo=ciclo_2, organizacao=organizacao)

    assert UniversoPesquisado.objects.filter(organizacao=organizacao).count() == 2
