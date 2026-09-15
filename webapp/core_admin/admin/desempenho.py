from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin
from core_admin.admin.mixins import AnoReferenciaAdminMixin
from core_admin.admin_site import site
from core_admin.models.desempenho import DesempenhoOrganizacao, Talento


@admin.register(DesempenhoOrganizacao, site=site)
class DesempenhoOrganizacaoAdmin(AnoReferenciaAdminMixin, BaseModelAdmin):
    list_display = ["organizacao", "ano_referencia_exibicao", "faturamento", "numero_empregados"]
    search_fields = ["organizacao__nome"]
    autocomplete_fields = ["organizacao"]

    @admin.display(description="Ano")
    def ano_referencia_exibicao(self, obj: DesempenhoOrganizacao) -> int | None:
        return obj.tempo.ano if obj.tempo_id else None


@admin.register(Talento, site=site)
class TalentoAdmin(AnoReferenciaAdminMixin, BaseModelAdmin):
    list_display = ["organizacao", "ano_referencia_exibicao", "pesquisadores_p_d", "mestres", "doutores"]
    search_fields = ["organizacao__nome"]
    autocomplete_fields = ["organizacao"]

    @admin.display(description="Ano")
    def ano_referencia_exibicao(self, obj: Talento) -> int | None:
        return obj.tempo.ano if obj.tempo_id else None
