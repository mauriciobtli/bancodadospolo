from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin, BaseTabularInline
from core_admin.admin_site import site
from core_admin.models.organizacoes import Organizacao
from core_admin.models.pesquisa import CicloColeta, CoberturaColeta, UniversoPesquisado

# UniversoPesquisado e CoberturaColeta têm chave primária composta
# (id_ciclo, id_organizacao) — o Django Admin não permite registrar
# standalone um modelo com PK composta (ImproperlyConfigured), então elas
# só são geridas como abas inline dentro de Ciclo de Coleta abaixo.


class UniversoPesquisadoInline(BaseTabularInline):
    model = UniversoPesquisado
    fk_name = "ciclo"
    fields = ["organizacao", "elegivel", "motivo_inelegibilidade"]
    autocomplete_fields = ["organizacao"]


class CoberturaColetaInline(BaseTabularInline):
    model = CoberturaColeta
    fk_name = "ciclo"
    fields = ["organizacao", "respondeu", "data_resposta", "instrumento"]
    autocomplete_fields = ["organizacao"]


@admin.register(CicloColeta, site=site)
class CicloColetaAdmin(BaseModelAdmin):
    list_display = ["nome", "ano_referencia", "tipo_cobertura", "data_inicio", "data_fim"]
    list_filter = ["tipo_cobertura", "ano_referencia"]
    search_fields = ["nome"]
    inlines = [UniversoPesquisadoInline, CoberturaColetaInline]
    actions = ["adicionar_organizacoes_area_atuacao"]

    @admin.action(description="Adicionar ao universo pesquisado as organizações ativas da área de atuação")
    def adicionar_organizacoes_area_atuacao(self, request, queryset):
        total = 0
        for ciclo in queryset:
            organizacoes = Organizacao.objects.filter(ativa=True, municipio__pertence_area_atuacao=True)
            existentes = set(
                UniversoPesquisado.objects.filter(ciclo=ciclo).values_list("organizacao_id", flat=True)
            )
            novas = [
                UniversoPesquisado(
                    ciclo=ciclo, organizacao=organizacao, elegivel=True,
                    fonte_dado="admin_web_acao_em_massa",
                )
                for organizacao in organizacoes
                if organizacao.id_organizacao not in existentes
            ]
            UniversoPesquisado.objects.bulk_create(novas)
            total += len(novas)
        self.message_user(request, f"{total} organização(ões) adicionada(s) ao universo pesquisado.")
