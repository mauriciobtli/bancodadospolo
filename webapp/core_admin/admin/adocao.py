from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin
from core_admin.admin.mixins import AnoReferenciaAdminMixin
from core_admin.admin_site import site
from core_admin.models.adocao import AdocaoTecnologica


@admin.register(AdocaoTecnologica, site=site)
class AdocaoTecnologicaAdmin(AnoReferenciaAdminMixin, BaseModelAdmin):
    list_display = ["organizacao", "tecnologia", "nivel_adocao", "ciclo", "ano_referencia_exibicao"]
    list_filter = ["nivel_adocao", "tecnologia", "ciclo"]
    search_fields = ["organizacao__nome"]
    autocomplete_fields = ["organizacao", "tecnologia", "ciclo"]

    @admin.display(description="Ano")
    def ano_referencia_exibicao(self, obj: AdocaoTecnologica) -> int | None:
        return obj.tempo.ano if obj.tempo_id else None
