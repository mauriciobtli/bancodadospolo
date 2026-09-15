from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin
from core_admin.admin_site import site
from core_admin.models.ecossistema import ConexaoEcossistema


@admin.register(ConexaoEcossistema, site=site)
class ConexaoEcossistemaAdmin(BaseModelAdmin):
    list_display = ["organizacao_origem", "organizacao_destino", "tipo_conexao", "data_inicio", "gerou_projeto", "gerou_inovacao"]
    list_filter = ["tipo_conexao", "gerou_projeto", "gerou_contrato", "gerou_inovacao"]
    search_fields = ["organizacao_origem__nome", "organizacao_destino__nome"]
    autocomplete_fields = ["organizacao_origem", "organizacao_destino", "projeto"]
