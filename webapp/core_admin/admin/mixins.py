"""Mixins reutilizados pelos ModelAdmins de core_admin.

A tradução de erro do Postgres (IntegrityError -> mensagem amigável) não
mora aqui: ModelAdmin.save_model()/save_formset() não têm seu
ValidationError capturado por _changeform_view em nenhuma versão atual do
Django (verificado no código-fonte instalado), então esse tratamento vive
no nível do AdminSite (ver core_admin.admin_site.PoloInovaleAdminSite.admin_view),
que envolve toda view e funciona também para os formsets de inline.

O que sobra aqui é só UX de widget: trocar "id_tempo" (FK para dim_tempo)
por um "Ano de referência" simples nos fatos anuais, seguindo a convenção
já documentada no DW (id_tempo aponta para 31/12 do ano).
"""
from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError


class AnoParaTempoFormField(forms.IntegerField):
    """Campo de formulário que se comporta como um IntegerField simples
    ("Ano de referência") mas, ao validar, resolve para a linha de
    dim_tempo do dia 31/12 daquele ano — a mesma convenção já usada pelos
    fatos anuais do DW. dim_tempo já tem essa linha seedada para
    2015-2035; um ano fora dessa faixa é rejeitado com uma mensagem clara."""

    def __init__(self, *, tempo_model, **kwargs):
        self.tempo_model = tempo_model
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if hasattr(value, "ano"):
            return value.ano
        return value

    def clean(self, value):
        ano = super().clean(value)
        if ano in self.empty_values:
            return None
        try:
            return self.tempo_model.objects.get(pk=ano * 10000 + 1231)
        except self.tempo_model.DoesNotExist:
            raise ValidationError(f"Ano {ano} fora do calendário disponível (2015-2035).") from None


class AnoReferenciaAdminMixin:
    """Troca o WIDGET do campo FK `campo_tempo` (aponta para dim_tempo) por
    um "Ano de referência" simples — o campo continua sendo o mesmo campo
    real do modelo (só o form field muda), então nada de especial é
    necessário em `fields`/`fieldsets`: o Django trata como qualquer outro
    campo do formulário."""

    campo_tempo = "tempo"
    ano_minimo = 2015
    ano_maximo = 2035

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == self.campo_tempo:
            return AnoParaTempoFormField(
                tempo_model=db_field.remote_field.model,
                label="Ano de referência",
                help_text="Registrado internamente como 31/12 deste ano (convenção do calendário do DW).",
                min_value=self.ano_minimo,
                max_value=self.ano_maximo,
                required=not db_field.blank,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
