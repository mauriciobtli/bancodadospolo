"""Permissões nativas dos 4 grupos criados pela migration
core_admin.0001_initial (Cadastro/Contatos/Importação/Leitura).

Cobre diretamente os itens 3 e 4 do pedido de revisão de segurança: a
permissão customizada `pode_importar_dados` deve pertencer
exclusivamente ao grupo "Importação" (e a superusuários), e nenhum grupo
além de "Contatos" pode ter qualquer permissão sobre ContatoOrganizacao
(dado pessoal, LGPD).
"""
from __future__ import annotations

import pytest
from django.contrib.auth.models import Group

pytestmark = pytest.mark.django_db

NOMES_GRUPOS = ("Leitura", "Cadastro", "Contatos", "Importação")


def test_grupos_criados_pela_migration():
    nomes = set(Group.objects.values_list("name", flat=True))
    assert set(NOMES_GRUPOS) <= nomes


def test_pode_importar_dados_e_exclusiva_do_grupo_importacao(grupo):
    for nome in ("Leitura", "Cadastro", "Contatos"):
        assert not grupo(nome).permissions.filter(codename="pode_importar_dados").exists(), (
            f"grupo {nome!r} não deveria ter a permissão pode_importar_dados"
        )
    assert grupo("Importação").permissions.filter(codename="pode_importar_dados").exists()


def test_cadastro_tem_crud_amplo_mas_nao_importa_nem_ve_contato(grupo):
    cadastro = grupo("Cadastro")
    codenames = set(cadastro.permissions.values_list("codename", flat=True))
    assert any(c.startswith("add_") for c in codenames)
    assert any(c.startswith("change_") for c in codenames)
    assert any(c.startswith("view_") for c in codenames)
    assert "pode_importar_dados" not in codenames
    assert not cadastro.permissions.filter(content_type__model="contatoorganizacao").exists()


def test_apenas_contatos_tem_permissao_sobre_contatoorganizacao(grupo):
    for nome in ("Leitura", "Cadastro", "Importação"):
        assert not grupo(nome).permissions.filter(content_type__model="contatoorganizacao").exists(), (
            f"grupo {nome!r} não deveria ter permissão sobre ContatoOrganizacao"
        )
    permissoes_contatos = set(
        grupo("Contatos").permissions.filter(content_type__model="contatoorganizacao").values_list(
            "codename", flat=True
        )
    )
    assert {"view_contatoorganizacao", "add_contatoorganizacao", "change_contatoorganizacao"} <= permissoes_contatos


def test_leitura_so_tem_permissoes_de_visualizacao(grupo):
    codenames = set(grupo("Leitura").permissions.values_list("codename", flat=True))
    assert codenames, "grupo Leitura deveria ter ao menos uma permissão"
    assert all(c.startswith("view_") for c in codenames)
    assert "pode_importar_dados" not in codenames


def test_importacao_so_tem_a_permissao_customizada(grupo):
    codenames = set(grupo("Importação").permissions.values_list("codename", flat=True))
    assert codenames == {"pode_importar_dados"}


def test_superusuario_tem_todas_as_permissoes(cria_usuario):
    admin = cria_usuario(superuser=True)
    assert admin.has_perm("core_admin.pode_importar_dados")
    assert admin.has_perm("core_admin.view_contatoorganizacao")
    assert admin.has_perm("core_admin.change_organizacao")


def test_usuario_cadastro_nao_tem_permissao_de_importar(cria_usuario):
    usuario = cria_usuario("Cadastro")
    assert not usuario.has_perm("core_admin.pode_importar_dados")
    assert usuario.has_perm("core_admin.change_organizacao")


def test_usuario_importacao_tem_permissao_de_importar(cria_usuario):
    usuario = cria_usuario("Importação")
    assert usuario.has_perm("core_admin.pode_importar_dados")
    assert not usuario.has_perm("core_admin.change_organizacao")
