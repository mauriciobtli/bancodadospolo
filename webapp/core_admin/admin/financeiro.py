from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin
from core_admin.admin.mixins import AnoReferenciaAdminMixin
from core_admin.admin_site import site
from core_admin.models.financeiro import InvestimentoInovacao


@admin.register(InvestimentoInovacao, site=site)
class InvestimentoInovacaoAdmin(AnoReferenciaAdminMixin, BaseModelAdmin):
    list_display = ["organizacao", "categoria", "fonte_recurso", "valor", "ano_referencia_exibicao"]
    list_filter = ["categoria", "fonte_recurso"]
    search_fields = ["organizacao__nome"]
    autocomplete_fields = ["organizacao", "fonte_recurso", "projeto"]

    @admin.display(description="Ano")
    def ano_referencia_exibicao(self, obj: InvestimentoInovacao) -> int | None:
        return obj.tempo.ano if obj.tempo_id else None
