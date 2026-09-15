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
        """Controla o que aparece no campo. Três formatos possíveis chegam
        aqui, dependendo do caminho de renderização do Django Admin:
        - criação (sem instância): None/"" (empty_values);
        - edição: model_to_dict() resolve o FK para o valor bruto da PK
          (int id_tempo, ex. 20241231), não para uma instância de Tempo;
        - reexibição após erro de validação (outro campo inválido no
          mesmo POST): o valor bruto SUBMETIDO pelo usuário, que já é o
          ano digitado (ex. "2024"), não um id_tempo.
        Distingue os dois formatos numéricos pela ordem de grandeza: anos
        vão de 2015 a 2035 (4 dígitos); id_tempo é sempre AAAAMMDD
        (8 dígitos, sempre > 9999)."""
        if value in self.empty_values:
            return value
        if hasattr(value, "ano"):
            return value.ano
        try:
            numero = int(value)
        except (TypeError, ValueError):
            return value
        return numero // 10000 if numero > 9999 else numero

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
