from __future__ import annotations

from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.organizacoes import Organizacao


class CicloColeta(TimestampedModel, FonteDadoModel):
    id_ciclo = models.BigAutoField(primary_key=True, db_column="id_ciclo")
    nome = models.TextField()
    ano_referencia = models.SmallIntegerField(verbose_name="Ano de referência")
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    tipo_cobertura = models.TextField(choices=dominios.TIPO_COBERTURA_CICLO, default="amostral", verbose_name="Tipo de cobertura")
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"core"."ciclo_coleta"'
        verbose_name = "Ciclo de coleta"
        verbose_name_plural = "Ciclos de coleta"
        ordering = ["-ano_referencia", "nome"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.ano_referencia})"


class UniversoPesquisado(TimestampedModel, FonteDadoModel):
    """core.universo_pesquisado — sampling frame de um ciclo. Uma
    organizacao so pode ter cobertura registrada (CoberturaColeta) se
    antes estiver aqui (FK composta no banco)."""

    pk = models.CompositePrimaryKey("ciclo", "organizacao")
    ciclo = models.ForeignKey(CicloColeta, db_column="id_ciclo", on_delete=models.CASCADE, related_name="universo_pesquisado")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="participacoes_em_universo",
    )
    elegivel = models.BooleanField(default=True)
    motivo_inelegibilidade = models.TextField(null=True, blank=True, verbose_name="Motivo de inelegibilidade")

    class Meta:
        managed = False
        db_table = '"core"."universo_pesquisado"'
        verbose_name = "Organização no universo pesquisado"
        verbose_name_plural = "Universo pesquisado"

    def __str__(self) -> str:
        return f"{self.organizacao} — {self.ciclo}"


class CoberturaColeta(TimestampedModel, FonteDadoModel):
    """core.cobertura_coleta — quem respondeu. Só pode existir cobertura
    para um par (ciclo, organização) já presente em UniversoPesquisado."""

    pk = models.CompositePrimaryKey("ciclo", "organizacao")
    ciclo = models.ForeignKey(CicloColeta, db_column="id_ciclo", on_delete=models.CASCADE, related_name="cobertura_coleta")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="coberturas_de_coleta",
    )
    respondeu = models.BooleanField()
    data_resposta = models.DateField(null=True, blank=True, verbose_name="Data de resposta")
    instrumento = models.TextField(null=True, blank=True, help_text="Ex.: formulário, entrevista, planilha.")
    observacao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"core"."cobertura_coleta"'
        verbose_name = "Cobertura de coleta"
        verbose_name_plural = "Cobertura de coleta"

    def __str__(self) -> str:
        return f"{self.organizacao} — {self.ciclo} ({'respondeu' if self.respondeu else 'não respondeu'})"
