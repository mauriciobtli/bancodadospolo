from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.dimensoes import Municipio, Setor
from etl.validators.cnpj import is_valid_cnpj, normalize_cnpj


class Organizacao(TimestampedModel, FonteDadoModel):
    """core.dim_organizacao — apenas dados públicos/institucionais. Dados
    pessoais de contato ficam em ContatoOrganizacao, isolados por permissão
    (grupo "Contatos")."""

    id_organizacao = models.BigAutoField(primary_key=True, db_column="id_organizacao")
    nome = models.TextField()
    nome_fantasia = models.TextField(null=True, blank=True, verbose_name="Nome fantasia")
    cnpj = models.CharField(max_length=14, null=True, blank=True, unique=True, verbose_name="CNPJ")
    tipo_organizacao = models.TextField(choices=dominios.TIPO_ORGANIZACAO, verbose_name="Tipo de organização")
    municipio = models.ForeignKey(
        Municipio, db_column="id_municipio", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="organizacoes", verbose_name="Município",
    )
    setor = models.ForeignKey(
        Setor, db_column="id_setor", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="organizacoes", verbose_name="Setor econômico",
    )
    porte = models.TextField(choices=dominios.PORTE, default="nao_informado")
    ano_fundacao = models.SmallIntegerField(null=True, blank=True, verbose_name="Ano de fundação")
    site = models.TextField(null=True, blank=True)
    ativa = models.BooleanField(default=True)
    data_entrada_ecossistema = models.DateField(null=True, blank=True, verbose_name="Data de entrada no ecossistema")
    data_saida_ecossistema = models.DateField(null=True, blank=True, verbose_name="Data de saída do ecossistema")
    motivo_saida = models.TextField(
        choices=dominios.MOTIVO_SAIDA_ORGANIZACAO, null=True, blank=True, verbose_name="Motivo da saída",
    )
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."dim_organizacao"'
        verbose_name = "Organização"
        verbose_name_plural = "Organizações"
        ordering = ["nome"]
        permissions = [("pode_importar_dados", "Pode importar dados via CSV/XLSX")]

    def __str__(self) -> str:
        return self.nome

    def clean(self) -> None:
        super().clean()
        if self.cnpj:
            cnpj_normalizado = normalize_cnpj(self.cnpj)
            if not is_valid_cnpj(cnpj_normalizado):
                raise ValidationError({"cnpj": "CNPJ inválido (dígito verificador não confere)."})
            self.cnpj = cnpj_normalizado


class ContatoOrganizacao(TimestampedModel, FonteDadoModel):
    """core.contato_organizacao — dado pessoal (LGPD). Acesso restrito ao
    grupo "Contatos" via permissões nativas do Django (ver
    core_admin/admin/organizacoes.py e a migration 0002_grupos_e_permissoes)."""

    id_contato = models.BigAutoField(primary_key=True, db_column="id_contato")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.CASCADE, related_name="contatos",
    )
    nome_contato = models.TextField(null=True, blank=True, verbose_name="Nome do contato")
    email = models.TextField(null=True, blank=True)
    telefone = models.TextField(null=True, blank=True)
    cargo = models.TextField(null=True, blank=True)
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."contato_organizacao"'
        verbose_name = "Contato da organização"
        verbose_name_plural = "Contatos das organizações"

    def __str__(self) -> str:
        return self.nome_contato or f"Contato #{self.pk}"
