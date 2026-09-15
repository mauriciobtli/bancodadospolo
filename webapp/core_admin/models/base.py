"""Infraestrutura comum aos modelos managed=False de core.*.

Todos os modelos deste app representam tabelas que ja existem no banco
(criadas e versionadas pelo Alembic, fora do Django). `managed = False`
garante que `manage.py migrate`/`makemigrations` nunca tenta criar, alterar
ou apagar essas tabelas — o Django so as descreve para gerar formularios e
consultas.
"""
from __future__ import annotations

from django.db import models
from django.db.models.functions import Now

FONTE_DADO_PADRAO = "admin_web"


class TimestampedModel(models.Model):
    """criado_em/atualizado_em existem em quase toda tabela core.* (ver
    convencao no README). db_default=Now() deixa o PRÓPRIO Postgres
    preencher o valor (mesmo DEFAULT now() das colunas) — o Django nunca
    inventa um horario proprio nem duplica essa regra."""

    criado_em = models.DateTimeField(db_default=Now(), editable=False)
    atualizado_em = models.DateTimeField(db_default=Now(), editable=False)

    class Meta:
        abstract = True


class FonteDadoModel(models.Model):
    """fonte_dado e obrigatorio em toda tabela operacional (rastreabilidade
    da carga). Registros criados manualmente pelo admin web sao marcados
    com 'admin_web' por padrao, mas o campo continua editavel."""

    fonte_dado = models.TextField(default=FONTE_DADO_PADRAO, verbose_name="Fonte do dado")

    class Meta:
        abstract = True
