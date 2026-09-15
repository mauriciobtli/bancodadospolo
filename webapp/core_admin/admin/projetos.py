from __future__ import annotations

from django.contrib import admin

from core_admin.admin.base import BaseModelAdmin, BaseTabularInline
from core_admin.admin_site import site
from core_admin.dominios import PAPEL_PROJETO_PARTICIPANTE
from core_admin.models.projetos import ParticipanteProjeto, Projeto, TecnologiaProjeto


class ParticipanteProjetoInline(BaseTabularInline):
    """'lider' nunca aparece como opção aqui: quem lidera o projeto é
    definido pelo campo "Organização líder" do próprio projeto (a fonte de
    verdade), e o banco sincroniza esta tabela automaticamente. Tentar
    gravar papel=lider direto por aqui seria rejeitado pelo banco."""

    model = ParticipanteProjeto
    fk_name = "projeto"
    fields = ["organizacao", "papel", "data_entrada", "data_saida", "fonte_dado"]
    autocomplete_fields = ["organizacao"]

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "papel":
            kwargs["choices"] = PAPEL_PROJETO_PARTICIPANTE
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_queryset(self, request):
        # A linha papel='lider' (gerida pelo trigger) fica visível só no
        # campo "Organização líder" do projeto, para não confundir com um
        # participante editável nesta aba.
        return super().get_queryset(request).exclude(papel="lider")


class TecnologiaProjetoInline(BaseTabularInline):
    """'principal' é somente leitura aqui: para trocar a tecnologia
    principal, edite o campo "Tecnologia principal" do próprio projeto — o
    banco sincroniza esta tabela automaticamente."""

    model = TecnologiaProjeto
    fields = ["tecnologia", "principal"]
    readonly_fields = ["principal"]
    autocomplete_fields = ["tecnologia"]


@admin.register(Projeto, site=site)
class ProjetoAdmin(BaseModelAdmin):
    list_display = ["nome", "organizacao_lider", "status", "data_inicio", "valor_total"]
    list_filter = ["status", "setor", "tecnologia_principal"]
    search_fields = ["nome", "organizacao_lider__nome"]
    autocomplete_fields = ["organizacao_lider", "fonte_principal", "setor", "tecnologia_principal", "problema_alvo"]
    inlines = [ParticipanteProjetoInline, TecnologiaProjetoInline]
    fieldsets = [
        (None, {"fields": ["nome", "descricao", "organizacao_lider", "status"]}),
        ("Cronograma e valor", {"fields": ["data_inicio", "data_fim_prevista", "data_fim_real", "valor_total"]}),
        (
            "Classificação",
            {"fields": ["fonte_principal", "setor", "tecnologia_principal", "problema_alvo", "mercado_alvo"]},
        ),
        ("Direcionalidade", {"fields": ["sustentabilidade", "automacao", "impacto_trabalho"]}),
        ("Rastreabilidade", {"fields": ["fonte_dado", "data_coleta"], "classes": ["collapse"]}),
    ]
