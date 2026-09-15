from __future__ import annotations

from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.organizacoes import Organizacao
from core_admin.models.projetos import Projeto


class PropriedadeIntelectual(TimestampedModel, FonteDadoModel):
    id_pi = models.BigAutoField(primary_key=True, db_column="id_pi")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="propriedades_intelectuais",
    )
    projeto = models.ForeignKey(
        Projeto, db_column="id_projeto", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="propriedades_intelectuais",
    )
    tipo_pi = models.TextField(choices=dominios.TIPO_PI, verbose_name="Tipo de PI")
    titulo = models.TextField()
    numero_registro = models.TextField(null=True, blank=True, verbose_name="Número de registro")
    data_deposito = models.DateField(null=True, blank=True, verbose_name="Data de depósito")
    data_concessao = models.DateField(null=True, blank=True, verbose_name="Data de concessão")
    status = models.TextField(choices=dominios.STATUS_PI, default="depositado")
    licenciada = models.BooleanField(default=False)
    receita_licenciamento = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True, verbose_name="Receita de licenciamento",
    )
    id_origem_externa = models.TextField(null=True, blank=True, verbose_name="Identificador de origem externa")
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."fato_propriedade_intelectual"'
        verbose_name = "Propriedade intelectual"
        verbose_name_plural = "Propriedade intelectual"
        ordering = ["-data_deposito"]

    def __str__(self) -> str:
        return self.titulo
