"""Sincronização automática (via trigger do Postgres — não reimplementada
aqui, só exercitada) entre core.projeto.id_organizacao_lider /
id_tecnologia_principal e as bridges bridge_projeto_organizacao /
bridge_projeto_tecnologia (ver db/schemas/23_core_bridges.sql). A
gravação passa pelo ORM do Django (managed=False), mas quem garante a
sincronização é o banco — o trigger dispara do mesmo jeito."""
from __future__ import annotations

import pytest

from core_admin.models.dimensoes import Tecnologia
from core_admin.models.organizacoes import Organizacao
from core_admin.models.projetos import ParticipanteProjeto, Projeto, TecnologiaProjeto

pytestmark = pytest.mark.django_db


@pytest.fixture
def organizacoes(db) -> tuple[Organizacao, Organizacao]:
    org_a = Organizacao.objects.create(nome="Organização Líder A", tipo_organizacao="empresa")
    org_b = Organizacao.objects.create(nome="Organização Líder B", tipo_organizacao="empresa")
    return org_a, org_b


@pytest.fixture
def tecnologias(db) -> tuple[Tecnologia, Tecnologia]:
    tec_a = Tecnologia.objects.create(codigo="tec-teste-a", nome="Tecnologia Teste A")
    tec_b = Tecnologia.objects.create(codigo="tec-teste-b", nome="Tecnologia Teste B")
    return tec_a, tec_b


def test_criar_projeto_com_lider_sincroniza_bridge(organizacoes):
    org_a, _ = organizacoes
    projeto = Projeto.objects.create(nome="Projeto Teste Líder", organizacao_lider=org_a)

    linha_lider = ParticipanteProjeto.objects.get(projeto=projeto, papel="lider")
    assert linha_lider.organizacao_id == org_a.pk


def test_trocar_lider_do_projeto_atualiza_a_bridge(organizacoes):
    org_a, org_b = organizacoes
    projeto = Projeto.objects.create(nome="Projeto Teste Troca Líder", organizacao_lider=org_a)

    projeto.organizacao_lider = org_b
    projeto.save()

    assert not ParticipanteProjeto.objects.filter(projeto=projeto, papel="lider", organizacao=org_a).exists()
    assert ParticipanteProjeto.objects.filter(projeto=projeto, papel="lider", organizacao=org_b).exists()


def test_remover_lider_do_projeto_remove_a_linha_da_bridge(organizacoes):
    org_a, _ = organizacoes
    projeto = Projeto.objects.create(nome="Projeto Teste Remover Líder", organizacao_lider=org_a)
    assert ParticipanteProjeto.objects.filter(projeto=projeto, papel="lider").exists()

    projeto.organizacao_lider = None
    projeto.save()

    assert not ParticipanteProjeto.objects.filter(projeto=projeto, papel="lider").exists()


def test_editar_bridge_diretamente_com_papel_lider_divergente_e_rejeitado(organizacoes):
    from django.db import IntegrityError

    org_a, org_b = organizacoes
    projeto = Projeto.objects.create(nome="Projeto Teste Guarda Líder", organizacao_lider=org_a)

    with pytest.raises(IntegrityError):
        ParticipanteProjeto.objects.create(projeto=projeto, organizacao=org_b, papel="lider", fonte_dado="teste")


def test_criar_projeto_com_tecnologia_principal_sincroniza_bridge(tecnologias):
    tec_a, _ = tecnologias
    projeto = Projeto.objects.create(nome="Projeto Teste Tecnologia", tecnologia_principal=tec_a)

    linha = TecnologiaProjeto.objects.get(projeto=projeto, tecnologia=tec_a)
    assert linha.principal is True


def test_trocar_tecnologia_principal_atualiza_a_bridge(tecnologias):
    tec_a, tec_b = tecnologias
    projeto = Projeto.objects.create(nome="Projeto Teste Troca Tecnologia", tecnologia_principal=tec_a)

    projeto.tecnologia_principal = tec_b
    projeto.save()

    assert TecnologiaProjeto.objects.get(projeto=projeto, tecnologia=tec_a).principal is False
    assert TecnologiaProjeto.objects.get(projeto=projeto, tecnologia=tec_b).principal is True


def test_participante_com_papel_diferente_de_lider_nao_e_afetado_pelo_guard(organizacoes):
    org_a, org_b = organizacoes
    projeto = Projeto.objects.create(nome="Projeto Teste Participante", organizacao_lider=org_a)

    participante = ParticipanteProjeto.objects.create(
        projeto=projeto, organizacao=org_b, papel="parceiro", fonte_dado="teste"
    )
    assert participante.papel == "parceiro"
