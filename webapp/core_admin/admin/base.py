from __future__ import annotations

from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """ModelAdmin padrão de core_admin. A tradução de erros do banco em
    mensagem amigável é tratada no nível do AdminSite (ver
    core_admin.admin_site.PoloInovaleAdminSite.admin_view), não aqui."""


class BaseTabularInline(admin.TabularInline):
    extra = 0
