"""Cria os grupos de permissao do admin web (Cadastro, Contatos,
Importacao, Leitura) e atribui as permissoes nativas do Django por modelo.

Nao cria nem altera NENHUMA tabela: todos os modelos deste app sao
managed=False (representam tabelas ja existentes em core.*, geridas pelo
Alembic). A unica coisa "real" que esta migration cria sao linhas em
auth_group/auth_permission (no schema `app` do Django).

Restricao de acesso a contato_organizacao (dado pessoal/LGPD): nenhum
grupo, exceto "Contatos", recebe qualquer permissao sobre
ContatoOrganizacao — nem "Leitura". "Contatos" tambem recebe
view_quarentenaregistro, pois e o unico grupo autorizado a ver sem
mascara o dado pessoal que pode aparecer em
etl.quarentena_registro.dados_originais (ver
core_admin/admin/importacao_historico.py).

Restricao da permissao customizada "pode_importar_dados": pertence
EXCLUSIVAMENTE ao grupo "Importacao" (e a superusuarios, que ja tem todas
as permissoes por definicao do Django). "Cadastro" tem CRUD amplo mas NAO
deve poder disparar importacao em massa — acao de maior impacto/risco,
tratada como uma permissao a parte (ver core_admin/apps.py::pode_importar_dados
em Organizacao.Meta.permissions).
"""
from __future__ import annotations

from django.contrib.auth.management import create_permissions
from django.db import migrations

NOME_GRUPO_LEITURA = "Leitura"
NOME_GRUPO_CADASTRO = "Cadastro"
NOME_GRUPO_CONTATOS = "Contatos"
NOME_GRUPO_IMPORTACAO = "Importação"

MODELO_CONTATO = "contatoorganizacao"
MODELO_QUARENTENA = "quarentenaregistro"
CODENAME_IMPORTAR = "pode_importar_dados"


def criar_grupos_e_permissoes(apps, schema_editor):
    # As permissions de core_admin (incluindo a custom "pode_importar_dados")
    # so sao criadas automaticamente pelo post_migrate signal ao FINAL de
    # todo o comando `migrate` — antecipamos aqui via create_permissions
    # (com o app registry REAL, nao o historico) para poder atribui-las
    # aos grupos dentro desta mesma migration.
    from django.apps import apps as apps_reais

    create_permissions(apps_reais.get_app_config("core_admin"), verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    permissoes_core_admin = Permission.objects.filter(content_type__app_label="core_admin")
    permissoes_sem_contato = permissoes_core_admin.exclude(content_type__model=MODELO_CONTATO)
    permissoes_so_contato = permissoes_core_admin.filter(content_type__model=MODELO_CONTATO)

    grupo_leitura, _ = Group.objects.get_or_create(name=NOME_GRUPO_LEITURA)
    grupo_leitura.permissions.set(permissoes_sem_contato.filter(codename__startswith="view_"))

    grupo_cadastro, _ = Group.objects.get_or_create(name=NOME_GRUPO_CADASTRO)
    grupo_cadastro.permissions.set(permissoes_sem_contato.exclude(codename=CODENAME_IMPORTAR))

    # Alem do CRUD de ContatoOrganizacao, "Contatos" tambem pode VISUALIZAR
    # a quarentena (etl.quarentena_registro) sem mascara — e o unico grupo
    # com motivo legitimo de ver o dado pessoal bruto de uma linha
    # rejeitada (ex.: para reconciliar um contato manualmente). O
    # mascaramento de dados_originais para quem NAO tem esta permissao
    # esta em core_admin/admin/importacao_historico.py::QuarentenaRegistroAdmin.
    permissao_ver_quarentena = permissoes_core_admin.filter(
        content_type__model=MODELO_QUARENTENA, codename="view_quarentenaregistro"
    )

    grupo_contatos, _ = Group.objects.get_or_create(name=NOME_GRUPO_CONTATOS)
    grupo_contatos.permissions.set(list(permissoes_so_contato) + list(permissao_ver_quarentena))

    grupo_importacao, _ = Group.objects.get_or_create(name=NOME_GRUPO_IMPORTACAO)
    grupo_importacao.permissions.set(permissoes_core_admin.filter(codename="pode_importar_dados"))


def remover_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=[NOME_GRUPO_LEITURA, NOME_GRUPO_CADASTRO, NOME_GRUPO_CONTATOS, NOME_GRUPO_IMPORTACAO]
    ).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0001_initial"),
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(criar_grupos_e_permissoes, remover_grupos),
    ]
