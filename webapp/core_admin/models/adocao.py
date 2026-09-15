from __future__ import annotations

from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.dimensoes import Tecnologia, Tempo
from core_admin.models.organizacoes import Organizacao
from core_admin.models.pesquisa import CicloColeta


class AdocaoTecnologica(TimestampedModel, FonteDadoModel):
    """core.fato_adocao_tecnologica. Preencher "Ciclo de coleta" e o que
    permite esta medicao contar no denominador de
    mart.vw_adocao_tecnologia (respondentes elegiveis do ciclo) — sem
    ciclo, a medicao fica fora dos KPIs de cobertura."""

    id_fato = models.BigAutoField(primary_key=True, db_column="id_fato")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="adocoes_tecnologicas",
    )
    tecnologia = models.ForeignKey(
        Tecnologia, db_column="id_tecnologia", on_delete=models.RESTRICT, related_name="adocoes",
    )
    tempo = models.ForeignKey(Tempo, db_column="id_tempo", on_delete=models.RESTRICT, related_name="+")
    ciclo = models.ForeignKey(
        CicloColeta, db_column="id_ciclo", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="adocoes_tecnologicas", verbose_name="Ciclo de coleta",
    )
    nivel_adocao = models.SmallIntegerField(choices=dominios.NIVEL_ADOCAO, verbose_name="Nível de adoção")
    ano_inicio_uso = models.SmallIntegerField(null=True, blank=True, verbose_name="Ano de início de uso")
    area_aplicacao = models.TextField(null=True, blank=True, verbose_name="Área de aplicação")
    observacao = models.TextField(null=True, blank=True)
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."fato_adocao_tecnologica"'
        verbose_name = "Adoção tecnológica"
        verbose_name_plural = "Adoção tecnológica"
        ordering = ["-tempo__data"]

    def __str__(self) -> str:
        return f"{self.organizacao} — {self.tecnologia} (nível {self.nivel_adocao})"
