from __future__ import annotations

from django.db import models

from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.dimensoes import Tempo
from core_admin.models.organizacoes import Organizacao


class DesempenhoOrganizacao(TimestampedModel, FonteDadoModel):
    """core.fato_desempenho_organizacao. investimento_p_d aqui e a FONTE DE
    VERDADE do KPI de intensidade de P&D (autodeclarado, mesmo grao do
    faturamento) — ver InvestimentoInovacao para o detalhamento
    categorizado, que e uma metrica DIFERENTE (não somar)."""

    id_fato = models.BigAutoField(primary_key=True, db_column="id_fato")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="desempenhos_anuais",
    )
    tempo = models.ForeignKey(Tempo, db_column="id_tempo", on_delete=models.RESTRICT, related_name="+")
    faturamento = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    numero_empregados = models.IntegerField(null=True, blank=True, verbose_name="Número de empregados")
    numero_empregados_tecnologia = models.IntegerField(
        null=True, blank=True, verbose_name="Número de empregados em tecnologia",
    )
    exportacoes = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    receita_produtos_novos = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True, verbose_name="Receita de produtos/serviços novos",
    )
    investimento_p_d = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True, verbose_name="Investimento em P&D (autodeclarado)",
    )
    custos_reduzidos_por_inovacao = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True, verbose_name="Custos reduzidos por inovação",
    )
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."fato_desempenho_organizacao"'
        verbose_name = "Desempenho anual da organização"
        verbose_name_plural = "Desempenho anual das organizações"
        ordering = ["-tempo__data"]

    def __str__(self) -> str:
        return f"{self.organizacao} — {self.tempo.ano if self.tempo_id else ''}"


class Talento(TimestampedModel, FonteDadoModel):
    """core.fato_talento — capital humano e conhecimento."""

    id_fato = models.BigAutoField(primary_key=True, db_column="id_fato")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="talentos",
    )
    tempo = models.ForeignKey(Tempo, db_column="id_tempo", on_delete=models.RESTRICT, related_name="+")
    pesquisadores_p_d = models.IntegerField(default=0, verbose_name="Pesquisadores em P&D")
    mestres = models.IntegerField(default=0)
    doutores = models.IntegerField(default=0)
    profissionais_stem = models.IntegerField(default=0, verbose_name="Profissionais STEM")
    pessoas_capacitadas = models.IntegerField(default=0)
    novas_contratacoes_qualificadas = models.IntegerField(default=0, verbose_name="Novas contratações qualificadas")
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."fato_talento"'
        verbose_name = "Capital humano / talento"
        verbose_name_plural = "Capital humano / talentos"
        ordering = ["-tempo__data"]

    def __str__(self) -> str:
        return f"{self.organizacao} — {self.tempo.ano if self.tempo_id else ''}"
