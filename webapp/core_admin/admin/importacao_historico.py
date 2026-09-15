from __future__ import annotations

from django.contrib import admin

from core_admin.admin_site import site
from core_admin.models.etl_historico import EtlExecucao, QuarentenaRegistro

# Colunas de raw.organizacoes que carregam dado pessoal (LGPD): quando uma
# linha e rejeitada, elas acabam integralmente em
# etl.quarentena_registro.dados_originais (dict bruto da linha raw — ver
# etl/pipeline.py::processar_organizacoes). Quem nao tem a permissao nativa
# sobre ContatoOrganizacao (grupo "Contatos") nao pode ver esses valores,
# nem aqui na quarentena.
CAMPOS_PESSOAIS_EM_DADOS_ORIGINAIS = {"nome_contato", "email_contato", "telefone_contato", "cargo_contato"}
PERMISSAO_VER_CONTATOS = "core_admin.view_contatoorganizacao"
MASCARA = "••• (dado pessoal oculto — requer permissão de Contatos)"


def _mascarar_dados_pessoais(dados_originais: dict | None) -> dict | None:
    if not dados_originais:
        return dados_originais
    mascarado = dict(dados_originais)
    for campo in CAMPOS_PESSOAIS_EM_DADOS_ORIGINAIS:
        if mascarado.get(campo):
            mascarado[campo] = MASCARA
    return mascarado


class SomenteLeituraAdminMixin:
    """django_app só tem SELECT no schema etl — o admin reflete isso: sem
    adicionar, editar ou apagar, só consultar."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EtlExecucao, site=site)
class EtlExecucaoAdmin(SomenteLeituraAdminMixin, admin.ModelAdmin):
    list_display = ["entidade_alvo", "tipo_fonte", "status", "iniciado_em", "registros_lidos", "registros_inseridos", "registros_atualizados", "registros_rejeitados"]
    list_filter = ["status", "tipo_fonte", "entidade_alvo"]
    search_fields = ["arquivo_fonte", "entidade_alvo"]
    date_hierarchy = "iniciado_em"


@admin.register(QuarentenaRegistro, site=site)
class QuarentenaRegistroAdmin(SomenteLeituraAdminMixin, admin.ModelAdmin):
    """`dados_originais` pode conter nome/e-mail/telefone/cargo de contato
    (ver CAMPOS_PESSOAIS_EM_DADOS_ORIGINAIS acima) — mascarados aqui para
    quem não tem a permissão nativa sobre ContatoOrganizacao.

    A mascara e aplicada sobrescrevendo o ATRIBUTO do objeto retornado por
    get_object (uma instancia nova por requisicao, nunca compartilhada
    entre threads/usuarios), nao um cache ou atributo da classe ModelAdmin
    — o Django Admin le o valor de dados_originais direto de
    `self.form.instance` ao renderizar o campo somente-leitura
    (admin.helpers.AdminReadonlyField.contents), entao mascarar aqui é
    suficiente e não há caminho para o dado bruto vazar na tela de
    detalhe. list_display também nunca inclui dados_originais."""

    list_display = ["entidade", "motivo_rejeicao", "resolvido", "criado_em", "execucao"]
    list_filter = ["entidade", "resolvido"]
    search_fields = ["motivo_rejeicao"]

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj is not None and not request.user.has_perm(PERMISSAO_VER_CONTATOS):
            obj.dados_originais = _mascarar_dados_pessoais(obj.dados_originais)
        return obj
