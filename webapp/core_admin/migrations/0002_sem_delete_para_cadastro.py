"""Segunda rodada de revisão de segurança: remove DELETE do grupo
"Cadastro" e cria o grupo "Administrador de Dados" para exclusões
excepcionais.

O banco tem natureza histórica (fatos anuais, importações, séries de
pesquisa) — usuários operacionais não devem poder apagar registros
fisicamente no dia a dia. "Cadastro" passa a ter só view/add/change.
Quem precisar apagar algo excepcionalmente é adicionado TAMBÉM ao grupo
"Administrador de Dados" (que só tem permissões delete_*, nada de
view/add/change — é sempre combinado com "Cadastro" ou "Leitura").

Esta é uma migration INCREMENTAL, não uma reescrita de 0001_initial: ela
roda por cima de qualquer estado que a 0001 já tenha deixado (inclusive
uma 0001 aplicada antes desta correção, quando "Cadastro" ainda recebia
delete_*), normalizando o resultado final independente do histórico.
Nunca mexe em ContatoOrganizacao (grupo "Contatos" continua sendo o
único dono daquele CRUD, delete incluído) nem em
EtlExecucao/QuarentenaRegistro (histórico de importação: nunca
apagável por ninguém pelo admin, ver SomenteLeituraAdminMixin).
"""
from __future__ import annotations

from django.db import migrations

NOME_GRUPO_CADASTRO = "Cadastro"
NOME_GRUPO_ADMINISTRADOR_DADOS = "Administrador de Dados"

MODELO_CONTATO = "contatoorganizacao"
MODELOS_SEM_DELETE_OPERACIONAL = {"quarentenaregistro", "etlexecucao"}


def normalizar_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    permissoes_core_admin = Permission.objects.filter(content_type__app_label="core_admin")
    permissoes_delete = permissoes_core_admin.filter(codename__startswith="delete_")

    grupo_cadastro, _ = Group.objects.get_or_create(name=NOME_GRUPO_CADASTRO)
    grupo_cadastro.permissions.remove(*permissoes_delete)

    permissoes_delete_administraveis = permissoes_delete.exclude(
        content_type__model=MODELO_CONTATO
    ).exclude(content_type__model__in=MODELOS_SEM_DELETE_OPERACIONAL)

    grupo_administrador_dados, _ = Group.objects.get_or_create(name=NOME_GRUPO_ADMINISTRADOR_DADOS)
    grupo_administrador_dados.permissions.set(permissoes_delete_administraveis)


def reverter(apps, schema_editor):
    """Best effort: devolve delete_* a "Cadastro" (estado original da
    0001) e remove o grupo "Administrador de Dados"."""
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    permissoes_core_admin = Permission.objects.filter(content_type__app_label="core_admin")
    permissoes_sem_contato = permissoes_core_admin.exclude(content_type__model=MODELO_CONTATO)

    try:
        grupo_cadastro = Group.objects.get(name=NOME_GRUPO_CADASTRO)
    except Group.DoesNotExist:
        pass
    else:
        grupo_cadastro.permissions.add(*permissoes_sem_contato.exclude(codename="pode_importar_dados"))

    Group.objects.filter(name=NOME_GRUPO_ADMINISTRADOR_DADOS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core_admin", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(normalizar_grupos, reverter),
    ]
