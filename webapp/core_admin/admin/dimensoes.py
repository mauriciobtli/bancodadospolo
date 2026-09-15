from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin
from core_admin.admin_site import site
from core_admin.models.dimensoes import (
    FonteRecurso,
    GrauNovidade,
    Municipio,
    ProblemaAlvo,
    Setor,
    Tecnologia,
    TipoInovacao,
)


@admin.register(Municipio, site=site)
class MunicipioAdmin(BaseModelAdmin):
    list_display = ["nome", "uf", "regiao", "pertence_area_atuacao", "codigo_ibge"]
    list_filter = ["uf", "regiao", "pertence_area_atuacao"]
    search_fields = ["nome", "codigo_ibge"]


@admin.register(Setor, site=site)
class SetorAdmin(BaseModelAdmin):
    list_display = ["nome", "codigo"]
    search_fields = ["nome", "codigo"]


@admin.register(Tecnologia, site=site)
class TecnologiaAdmin(BaseModelAdmin):
    list_display = ["nome", "codigo"]
    search_fields = ["nome", "codigo"]


@admin.register(TipoInovacao, site=site)
class TipoInovacaoAdmin(BaseModelAdmin):
    list_display = ["nome", "codigo"]
    search_fields = ["nome", "codigo"]


@admin.register(GrauNovidade, site=site)
class GrauNovidadeAdmin(BaseModelAdmin):
    list_display = ["ordem", "nome", "codigo"]
    search_fields = ["nome", "codigo"]
    ordering = ["ordem"]


@admin.register(FonteRecurso, site=site)
class FonteRecursoAdmin(BaseModelAdmin):
    list_display = ["nome", "codigo"]
    search_fields = ["nome", "codigo"]


@admin.register(ProblemaAlvo, site=site)
class ProblemaAlvoAdmin(BaseModelAdmin):
    list_display = ["nome", "codigo"]
    search_fields = ["nome", "codigo"]
