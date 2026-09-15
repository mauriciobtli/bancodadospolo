from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin
from core_admin.admin_site import site
from core_admin.models.propriedade_intelectual import PropriedadeIntelectual


@admin.register(PropriedadeIntelectual, site=site)
class PropriedadeIntelectualAdmin(BaseModelAdmin):
    list_display = ["titulo", "organizacao", "tipo_pi", "status", "data_deposito", "licenciada"]
    list_filter = ["tipo_pi", "status", "licenciada"]
    search_fields = ["titulo", "numero_registro", "organizacao__nome"]
    autocomplete_fields = ["organizacao", "projeto"]
