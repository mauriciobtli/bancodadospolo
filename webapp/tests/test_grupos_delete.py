"""Ausência de DELETE para usuários operacionais (item 1 da revisão
pré-produção) e a migration incremental 0002_sem_delete_para_cadastro
(item 2) — sem reescrever 0001_initial.py.
"""
from __future__ import annotations

import importlib

import pytest
from django.apps import apps as apps_reais
from django.contrib.auth.models import Group, Permission

# Nomes de módulo de migration começam com dígito (convenção do Django),
# então não são identificadores Python válidos para `import ... as` — só
# importlib consegue carregar o módulo pelo nome literal do arquivo.
migration_0002 = importlib.import_module("core_admin.migrations.0002_sem_delete_para_cadastro")

pytestmark = pytest.mark.django_db

NOME_GRUPO_ADMINISTRADOR_DADOS = "Administrador de Dados"


def test_cadastro_nao_tem_nenhuma_permissao_delete(grupo):
    cadastro = grupo("Cadastro")
    assert not cadastro.permissions.filter(codename__startswith="delete_").exists()
    # e continua com view/add/change normalmente
    codenames = set(cadastro.permissions.values_list("codename", flat=True))
    assert any(c.startswith("add_") for c in codenames)
    assert any(c.startswith("change_") for c in codenames)
    assert any(c.startswith("view_") for c in codenames)


def test_grupo_administrador_de_dados_existe_e_so_tem_delete(grupo):
    administrador = grupo(NOME_GRUPO_ADMINISTRADOR_DADOS)
    codenames = set(administrador.permissions.values_list("codename", flat=True))
    assert codenames, "Administrador de Dados deveria ter ao menos uma permissão"
    assert all(c.startswith("delete_") for c in codenames)


def test_administrador_de_dados_nao_inclui_contato_nem_quarentena(grupo):
    administrador = grupo(NOME_GRUPO_ADMINISTRADOR_DADOS)
    assert not administrador.permissions.filter(content_type__model="contatoorganizacao").exists()
    assert not administrador.permissions.filter(content_type__model="quarentenaregistro").exists()
    assert not administrador.permissions.filter(content_type__model="etlexecucao").exists()
    assert administrador.permissions.filter(codename="delete_organizacao").exists()
    assert administrador.permissions.filter(codename="delete_projeto").exists()


def test_contatos_mantem_delete_contatoorganizacao(grupo):
    """A migration 0002 não mexe em ContatoOrganizacao: "Contatos"
    continua sendo o único dono daquele CRUD, exclusão incluída."""
    contatos = grupo("Contatos")
    assert contatos.permissions.filter(codename="delete_contatoorganizacao").exists()


def test_usuario_cadastro_mais_administrador_de_dados_tem_delete(cria_usuario):
    usuario = cria_usuario("Cadastro", NOME_GRUPO_ADMINISTRADOR_DADOS)
    assert usuario.has_perm("core_admin.delete_organizacao")
    assert usuario.has_perm("core_admin.change_organizacao")


def test_usuario_so_cadastro_nao_tem_delete(cria_usuario):
    usuario = cria_usuario("Cadastro")
    assert not usuario.has_perm("core_admin.delete_organizacao")


def test_migration_0002_e_idempotente_rodando_de_novo(db):
    """Rodar a função da migration mais de uma vez (o próprio cenário de
    reaplicar em cima de um ambiente que já a aplicou) não muda o
    resultado nem levanta erro."""
    migration_0002.normalizar_grupos(apps_reais, None)
    estado_1 = _snapshot_permissoes()

    migration_0002.normalizar_grupos(apps_reais, None)
    estado_2 = _snapshot_permissoes()

    assert estado_1 == estado_2


def test_migration_0002_conserta_ambiente_que_rodou_0001_antiga(db):
    """Simula um ambiente onde a 0001 antiga (antes desta correção) já
    tinha dado delete_organizacao ao Cadastro — a 0002 precisa remover
    isso ao rodar por cima, sem reescrever a 0001."""
    grupo_cadastro, _ = Group.objects.get_or_create(name="Cadastro")
    permissao_delete_organizacao = Permission.objects.get(
        content_type__app_label="core_admin", codename="delete_organizacao"
    )
    grupo_cadastro.permissions.add(permissao_delete_organizacao)
    assert grupo_cadastro.permissions.filter(codename="delete_organizacao").exists()

    migration_0002.normalizar_grupos(apps_reais, None)

    grupo_cadastro.refresh_from_db()
    assert not grupo_cadastro.permissions.filter(codename__startswith="delete_").exists()


def _snapshot_permissoes() -> dict[str, set[str]]:
    return {
        g.name: set(g.permissions.values_list("codename", flat=True))
        for g in Group.objects.filter(
            name__in=["Leitura", "Cadastro", "Contatos", "Importação", NOME_GRUPO_ADMINISTRADOR_DADOS]
        )
    }
