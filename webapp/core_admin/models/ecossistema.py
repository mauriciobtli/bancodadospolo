from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.organizacoes import Organizacao
from core_admin.models.projetos import Projeto


class ConexaoEcossistema(TimestampedModel, FonteDadoModel):
    id_conexao = models.BigAutoField(primary_key=True, db_column="id_conexao")
    organizacao_origem = models.ForeignKey(
        Organizacao, db_column="id_organizacao_origem", on_delete=models.RESTRICT,
        related_name="conexoes_como_origem", verbose_name="Organização de origem",
    )
    organizacao_destino = models.ForeignKey(
        Organizacao, db_column="id_organizacao_destino", on_delete=models.RESTRICT,
        related_name="conexoes_como_destino", verbose_name="Organização de destino",
    )
    tipo_conexao = models.TextField(choices=dominios.TIPO_CONEXAO, verbose_name="Tipo de conexão")
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    projeto = models.ForeignKey(
        Projeto, db_column="id_projeto", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="conexoes",
    )
    valor_financeiro = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name="Valor financeiro")
    gerou_projeto = models.BooleanField(default=False, verbose_name="Gerou projeto")
    gerou_contrato = models.BooleanField(default=False, verbose_name="Gerou contrato")
    gerou_inovacao = models.BooleanField(default=False, verbose_name="Gerou inovação")
    id_origem_externa = models.TextField(null=True, blank=True, verbose_name="Identificador de origem externa")
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."fato_conexao_ecossistema"'
        verbose_name = "Conexão do ecossistema"
        verbose_name_plural = "Conexões do ecossistema"
        ordering = ["-data_inicio"]

    def __str__(self) -> str:
        return f"{self.organizacao_origem} → {self.organizacao_destino} ({self.get_tipo_conexao_display()})"

    def clean(self) -> None:
        super().clean()
        if self.organizacao_origem_id and self.organizacao_origem_id == self.organizacao_destino_id:
            raise ValidationError("A organização de origem e destino não podem ser a mesma.")
