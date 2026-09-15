from __future__ import annotations

from django.db import models

from core_admin import dominios
from core_admin.models.base import TimestampedModel


class Tempo(models.Model):
    """core.dim_tempo — grao diario, populada pelo seed (2015-2035). O
    admin nao oferece cadastro manual: os formularios de fato usam um
    campo simples "Ano de referencia" que resolve para o dia 31/12 do ano
    (ver core_admin/admin/mixins.py), evitando expor esta tabela enorme
    como dropdown."""

    id_tempo = models.BigIntegerField(primary_key=True, db_column="id_tempo")
    data = models.DateField(unique=True)
    dia = models.SmallIntegerField()
    mes = models.SmallIntegerField()
    nome_mes = models.TextField()
    trimestre = models.SmallIntegerField()
    ano = models.SmallIntegerField()
    criado_em = models.DateTimeField(editable=False)

    class Meta:
        managed = False
        db_table = '"core"."dim_tempo"'
        verbose_name = "Data (calendário)"
        verbose_name_plural = "Calendário"

    def __str__(self) -> str:
        return self.data.isoformat()


class Municipio(TimestampedModel):
    id_municipio = models.BigAutoField(primary_key=True, db_column="id_municipio")
    codigo_ibge = models.CharField(max_length=7, unique=True, verbose_name="Código IBGE")
    nome = models.TextField()
    uf = models.CharField(max_length=2, verbose_name="UF")
    regiao = models.TextField(choices=dominios.REGIAO)
    pertence_area_atuacao = models.BooleanField(default=False, verbose_name="Pertence à área de atuação")
    fonte_dado = models.TextField(default="admin_web", verbose_name="Fonte do dado")
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."dim_municipio"'
        verbose_name = "Município"
        verbose_name_plural = "Municípios"
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.nome}/{self.uf}"


class Setor(TimestampedModel):
    id_setor = models.BigAutoField(primary_key=True, db_column="id_setor")
    codigo = models.TextField(unique=True)
    nome = models.TextField()
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"core"."dim_setor"'
        verbose_name = "Setor econômico"
        verbose_name_plural = "Setores econômicos"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Tecnologia(TimestampedModel):
    id_tecnologia = models.BigAutoField(primary_key=True, db_column="id_tecnologia")
    codigo = models.TextField(unique=True)
    nome = models.TextField()
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"core"."dim_tecnologia"'
        verbose_name = "Tecnologia"
        verbose_name_plural = "Tecnologias"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class TipoInovacao(TimestampedModel):
    id_tipo_inovacao = models.BigAutoField(primary_key=True, db_column="id_tipo_inovacao")
    codigo = models.TextField(unique=True)
    nome = models.TextField()

    class Meta:
        managed = False
        db_table = '"core"."dim_tipo_inovacao"'
        verbose_name = "Tipo de inovação"
        verbose_name_plural = "Tipos de inovação"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class GrauNovidade(TimestampedModel):
    id_grau_novidade = models.BigAutoField(primary_key=True, db_column="id_grau_novidade")
    codigo = models.TextField(unique=True)
    nome = models.TextField()
    ordem = models.SmallIntegerField(unique=True)

    class Meta:
        managed = False
        db_table = '"core"."dim_grau_novidade"'
        verbose_name = "Grau de novidade"
        verbose_name_plural = "Graus de novidade"
        ordering = ["ordem"]

    def __str__(self) -> str:
        return self.nome


class FonteRecurso(TimestampedModel):
    id_fonte_recurso = models.BigAutoField(primary_key=True, db_column="id_fonte_recurso")
    codigo = models.TextField(unique=True)
    nome = models.TextField()

    class Meta:
        managed = False
        db_table = '"core"."dim_fonte_recurso"'
        verbose_name = "Fonte de recurso"
        verbose_name_plural = "Fontes de recurso"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class ProblemaAlvo(TimestampedModel):
    id_problema_alvo = models.BigAutoField(primary_key=True, db_column="id_problema_alvo")
    codigo = models.TextField(unique=True)
    nome = models.TextField()

    class Meta:
        managed = False
        db_table = '"core"."dim_problema_alvo"'
        verbose_name = "Problema-alvo"
        verbose_name_plural = "Problemas-alvo"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
