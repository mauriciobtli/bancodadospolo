"""Leitura (somente leitura!) de etl.etl_execucao / etl.quarentena_registro.

django_app só tem SELECT no schema etl (ver db/roles/django_app.sql) — quem
grava ali é o ETL rodando com a role de administração, não o Django. Estes
modelos existem só para o admin web poder listar/consultar o histórico de
importações.
"""
from __future__ import annotations

from django.db import models


class EtlExecucao(models.Model):
    id_execucao = models.BigAutoField(primary_key=True, db_column="id_execucao")
    arquivo_fonte = models.TextField(verbose_name="Arquivo/fonte")
    tipo_fonte = models.TextField(verbose_name="Tipo de fonte")
    entidade_alvo = models.TextField(verbose_name="Entidade")
    iniciado_em = models.DateTimeField(verbose_name="Iniciado em")
    finalizado_em = models.DateTimeField(null=True, blank=True, verbose_name="Finalizado em")
    registros_lidos = models.IntegerField(verbose_name="Lidos")
    registros_inseridos = models.IntegerField(verbose_name="Inseridos")
    registros_atualizados = models.IntegerField(verbose_name="Atualizados")
    registros_rejeitados = models.IntegerField(verbose_name="Rejeitados")
    status = models.TextField()
    mensagem_erro = models.TextField(null=True, blank=True, verbose_name="Mensagem de erro")

    class Meta:
        managed = False
        db_table = '"etl"."etl_execucao"'
        verbose_name = "Execução de importação"
        verbose_name_plural = "Execuções de importação"
        ordering = ["-iniciado_em"]

    def __str__(self) -> str:
        return f"{self.entidade_alvo} — {self.iniciado_em:%d/%m/%Y %H:%M}"


class QuarentenaRegistro(models.Model):
    id_quarentena = models.BigAutoField(primary_key=True, db_column="id_quarentena")
    execucao = models.ForeignKey(
        EtlExecucao, db_column="id_execucao", on_delete=models.DO_NOTHING, related_name="quarentena",
    )
    entidade = models.TextField()
    linha_origem = models.IntegerField(null=True, blank=True, verbose_name="Linha de origem")
    dados_originais = models.JSONField(verbose_name="Dados originais")
    motivo_rejeicao = models.TextField(verbose_name="Motivo da rejeição")
    resolvido = models.BooleanField()
    resolvido_em = models.DateTimeField(null=True, blank=True, verbose_name="Resolvido em")
    criado_em = models.DateTimeField(editable=False)

    class Meta:
        managed = False
        db_table = '"etl"."quarentena_registro"'
        verbose_name = "Registro em quarentena"
        verbose_name_plural = "Quarentena"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.entidade} (execução #{self.execucao_id})"
