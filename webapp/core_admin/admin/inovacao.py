from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin, BaseTabularInline
from core_admin.admin_site import site
from core_admin.models.inovacao import Inovacao, TecnologiaInovacao


class TecnologiaInovacaoInline(BaseTabularInline):
    model = TecnologiaInovacao
    fields = ["tecnologia", "principal"]
    autocomplete_fields = ["tecnologia"]


@admin.register(Inovacao, site=site)
class InovacaoAdmin(BaseModelAdmin):
    list_display = ["nome", "organizacao", "tipo_inovacao", "grau_novidade", "status", "data_implementacao"]
    list_filter = ["status", "tipo_inovacao", "grau_novidade", "chegou_ao_mercado"]
    search_fields = ["nome", "organizacao__nome"]
    autocomplete_fields = ["organizacao", "projeto", "tipo_inovacao", "grau_novidade", "problema_alvo"]
    inlines = [TecnologiaInovacaoInline]
    fieldsets = [
        (None, {"fields": ["nome", "descricao", "organizacao", "projeto"]}),
        ("Classificação", {"fields": ["tipo_inovacao", "grau_novidade", "problema_alvo", "impacto_trabalho"]}),
        ("Linha do tempo e status", {"fields": ["data_inicio", "data_implementacao", "status", "chegou_ao_mercado", "mercado_alvo"]}),
        (
            "Resultados",
            {
                "fields": [
                    "receita_associada", "reducao_custo_estimada", "aumento_capacidade_percentual",
                    "empregos_criados", "empregos_qualificados_criados",
                ]
            },
        ),
        ("Rastreabilidade", {"fields": ["fonte_dado", "data_coleta", "id_origem_externa"], "classes": ["collapse"]}),
    ]
