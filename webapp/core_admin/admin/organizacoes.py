from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin, BaseTabularInline
from core_admin.admin_site import site
from core_admin.models.organizacoes import ContatoOrganizacao, Organizacao


class ContatoOrganizacaoInline(BaseTabularInline):
    """Só aparece/é editável para quem tem permissão sobre
    ContatoOrganizacao (grupo "Contatos") — o Django Admin já checa isso
    nativamente por inline, sem código extra aqui."""

    model = ContatoOrganizacao
    fields = ["nome_contato", "email", "telefone", "cargo", "fonte_dado"]


@admin.register(Organizacao, site=site)
class OrganizacaoAdmin(BaseModelAdmin):
    list_display = ["nome", "cnpj", "tipo_organizacao", "municipio", "setor", "porte", "ativa"]
    list_filter = ["tipo_organizacao", "porte", "ativa", "setor", "municipio__uf"]
    search_fields = ["nome", "nome_fantasia", "cnpj"]
    autocomplete_fields = ["municipio", "setor"]
    inlines = [ContatoOrganizacaoInline]
    fieldsets = [
        (None, {"fields": ["nome", "nome_fantasia", "cnpj", "tipo_organizacao", "site"]}),
        ("Classificação", {"fields": ["municipio", "setor", "porte", "ano_fundacao"]}),
        (
            "Ciclo de vida no ecossistema",
            {"fields": ["ativa", "data_entrada_ecossistema", "data_saida_ecossistema", "motivo_saida"]},
        ),
        ("Rastreabilidade", {"fields": ["fonte_dado", "data_coleta"], "classes": ["collapse"]}),
    ]


@admin.register(ContatoOrganizacao, site=site)
class ContatoOrganizacaoAdmin(BaseModelAdmin):
    """Tela dedicada, além da aba inline em Organização — útil para o
    grupo "Contatos" buscar/filtrar diretamente por pessoa."""

    list_display = ["nome_contato", "organizacao", "email", "telefone", "cargo"]
    search_fields = ["nome_contato", "email", "organizacao__nome"]
    autocomplete_fields = ["organizacao"]
