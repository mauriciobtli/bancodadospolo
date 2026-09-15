from __future__ import annotations

from django.contrib import admin

from core_admin.admin_site import site
from core_admin.models.etl_historico import EtlExecucao, QuarentenaRegistro


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
    list_display = ["entidade", "motivo_rejeicao", "resolvido", "criado_em", "execucao"]
    list_filter = ["entidade", "resolvido"]
    search_fields = ["motivo_rejeicao"]
