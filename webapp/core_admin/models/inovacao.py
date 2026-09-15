from __future__ import annotations

from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.dimensoes import GrauNovidade, ProblemaAlvo, Tecnologia, TipoInovacao
from core_admin.models.organizacoes import Organizacao
from core_admin.models.projetos import Projeto


class Inovacao(TimestampedModel, FonteDadoModel):
    id_inovacao = models.BigAutoField(primary_key=True, db_column="id_inovacao")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="inovacoes",
    )
    projeto = models.ForeignKey(
        Projeto, db_column="id_projeto", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="inovacoes",
    )
    nome = models.TextField()
    descricao = models.TextField(null=True, blank=True)
    tipo_inovacao = models.ForeignKey(
        TipoInovacao, db_column="id_tipo_inovacao", on_delete=models.RESTRICT,
        related_name="inovacoes", verbose_name="Tipo de inovação",
    )
    grau_novidade = models.ForeignKey(
        GrauNovidade, db_column="id_grau_novidade", on_delete=models.RESTRICT,
        related_name="inovacoes", verbose_name="Grau de novidade",
    )
    problema_alvo = models.ForeignKey(
        ProblemaAlvo, db_column="id_problema_alvo", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="inovacoes", verbose_name="Problema-alvo",
    )
    data_inicio = models.DateField(null=True, blank=True)
    data_implementacao = models.DateField(null=True, blank=True)
    status = models.TextField(choices=dominios.STATUS_INOVACAO, default="ideacao")
    chegou_ao_mercado = models.BooleanField(default=False, verbose_name="Chegou ao mercado")
    mercado_alvo = models.TextField(null=True, blank=True, verbose_name="Mercado-alvo")
    impacto_trabalho = models.TextField(choices=dominios.IMPACTO_TRABALHO, null=True, blank=True, verbose_name="Impacto no trabalho")
    receita_associada = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name="Receita associada")
    reducao_custo_estimada = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name="Redução de custo estimada")
    aumento_capacidade_percentual = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Aumento de capacidade (%)",
    )
    empregos_criados = models.IntegerField(default=0, verbose_name="Empregos criados")
    empregos_qualificados_criados = models.IntegerField(default=0, verbose_name="Empregos qualificados criados")
    id_origem_externa = models.TextField(
        null=True, blank=True, verbose_name="Identificador de origem externa",
        help_text="Preenchido pelo ETL para permitir reprocessamento idempotente; deixe em branco em cadastro manual.",
    )
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."fato_inovacao"'
        verbose_name = "Inovação"
        verbose_name_plural = "Inovações"
        ordering = ["-data_inicio", "nome"]

    def __str__(self) -> str:
        return self.nome


class TecnologiaInovacao(models.Model):
    """core.bridge_inovacao_tecnologia — N:N livre (sem trigger de
    sincronizacao; diferente das bridges de projeto, aqui 'principal' e
    editavel diretamente)."""

    pk = models.CompositePrimaryKey("inovacao", "tecnologia")
    inovacao = models.ForeignKey(Inovacao, db_column="id_inovacao", on_delete=models.CASCADE, related_name="tecnologias")
    tecnologia = models.ForeignKey(
        Tecnologia, db_column="id_tecnologia", on_delete=models.RESTRICT, related_name="inovacoes_que_usam",
    )
    principal = models.BooleanField(default=False)
    criado_em = models.DateTimeField(editable=False)

    class Meta:
        managed = False
        db_table = '"core"."bridge_inovacao_tecnologia"'
        verbose_name = "Tecnologia da inovação"
        verbose_name_plural = "Tecnologias da inovação"

    def __str__(self) -> str:
        return str(self.tecnologia)
