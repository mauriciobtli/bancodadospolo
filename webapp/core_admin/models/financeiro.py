from __future__ import annotations

from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.dimensoes import FonteRecurso, Tempo
from core_admin.models.organizacoes import Organizacao
from core_admin.models.projetos import Projeto


class InvestimentoInovacao(TimestampedModel, FonteDadoModel):
    """core.fato_investimento_inovacao. Fonte de verdade do detalhamento de
    P&D por fonte/projeto/tecnologia (categoria='p_d') — NAO confundir com
    DesempenhoOrganizacao.investimento_p_d (total anual autodeclarado, ver
    docs/views_e_kpis.md)."""

    id_fato = models.BigAutoField(primary_key=True, db_column="id_fato")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="investimentos",
    )
    tempo = models.ForeignKey(Tempo, db_column="id_tempo", on_delete=models.RESTRICT, related_name="+")
    fonte_recurso = models.ForeignKey(
        FonteRecurso, db_column="id_fonte_recurso", on_delete=models.RESTRICT,
        related_name="investimentos", verbose_name="Fonte de recurso",
    )
    projeto = models.ForeignKey(
        Projeto, db_column="id_projeto", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="investimentos",
        help_text="Opcional. Necessário para o investimento aparecer no detalhamento por tecnologia.",
    )
    categoria = models.TextField(choices=dominios.CATEGORIA_INVESTIMENTO)
    valor = models.DecimalField(max_digits=16, decimal_places=2)
    observacao = models.TextField(null=True, blank=True)
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."fato_investimento_inovacao"'
        verbose_name = "Investimento em inovação"
        verbose_name_plural = "Investimentos em inovação"
        ordering = ["-tempo__data"]

    def __str__(self) -> str:
        return f"{self.organizacao} — {self.get_categoria_display()} ({self.valor})"
