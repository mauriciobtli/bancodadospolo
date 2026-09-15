from __future__ import annotations

from django.db import models

from core_admin import dominios
from core_admin.models.base import FonteDadoModel, TimestampedModel
from core_admin.models.dimensoes import FonteRecurso, ProblemaAlvo, Setor, Tecnologia
from core_admin.models.organizacoes import Organizacao


class Projeto(TimestampedModel, FonteDadoModel):
    """core.projeto. organizacao_lider e tecnologia_principal sao a FONTE
    DE VERDADE (o banco sincroniza automaticamente as bridges abaixo via
    trigger — ver db/schemas/23_core_bridges.sql). Editar esses dois campos
    aqui e a UNICA forma valida de trocar o lider/tecnologia principal."""

    id_projeto = models.BigAutoField(primary_key=True, db_column="id_projeto")
    nome = models.TextField()
    descricao = models.TextField(null=True, blank=True)
    organizacao_lider = models.ForeignKey(
        Organizacao, db_column="id_organizacao_lider", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="projetos_liderados", verbose_name="Organização líder",
    )
    data_inicio = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True, verbose_name="Data de fim prevista")
    data_fim_real = models.DateField(null=True, blank=True, verbose_name="Data de fim real")
    status = models.TextField(choices=dominios.STATUS_PROJETO, default="planejado")
    valor_total = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True, verbose_name="Valor total (orçado)",
    )
    fonte_principal = models.ForeignKey(
        FonteRecurso, db_column="id_fonte_principal", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="projetos", verbose_name="Fonte de recurso principal",
    )
    setor = models.ForeignKey(
        Setor, db_column="id_setor", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="projetos", verbose_name="Setor",
    )
    tecnologia_principal = models.ForeignKey(
        Tecnologia, db_column="id_tecnologia_principal", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="projetos_principais", verbose_name="Tecnologia principal",
    )
    problema_alvo = models.ForeignKey(
        ProblemaAlvo, db_column="id_problema_alvo", on_delete=models.RESTRICT,
        null=True, blank=True, related_name="projetos", verbose_name="Problema-alvo",
    )
    sustentabilidade = models.BooleanField(null=True, blank=True)
    automacao = models.BooleanField(null=True, blank=True)
    impacto_trabalho = models.TextField(choices=dominios.IMPACTO_TRABALHO, null=True, blank=True, verbose_name="Impacto no trabalho")
    mercado_alvo = models.TextField(null=True, blank=True, verbose_name="Mercado-alvo")
    data_coleta = models.DateField(null=True, blank=True, verbose_name="Data de coleta")

    class Meta:
        managed = False
        db_table = '"core"."projeto"'
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ["-data_inicio", "nome"]

    def __str__(self) -> str:
        return self.nome


class ParticipanteProjeto(models.Model):
    """core.bridge_projeto_organizacao. A linha papel='lider' e mantida
    automaticamente pelo banco a partir de Projeto.organizacao_lider — o
    admin nunca oferece 'lider' como opcao aqui (ver
    core_admin/admin/projetos.py)."""

    pk = models.CompositePrimaryKey("projeto", "organizacao", "papel")
    projeto = models.ForeignKey(Projeto, db_column="id_projeto", on_delete=models.CASCADE, related_name="participantes")
    organizacao = models.ForeignKey(
        Organizacao, db_column="id_organizacao", on_delete=models.RESTRICT, related_name="participacoes_em_projetos",
    )
    papel = models.TextField(choices=dominios.PAPEL_PROJETO_TODOS)
    data_entrada = models.DateField(null=True, blank=True)
    data_saida = models.DateField(null=True, blank=True)
    fonte_dado = models.TextField(default="admin_web")
    criado_em = models.DateTimeField(editable=False)

    class Meta:
        managed = False
        db_table = '"core"."bridge_projeto_organizacao"'
        verbose_name = "Participante do projeto"
        verbose_name_plural = "Participantes do projeto"

    def __str__(self) -> str:
        return f"{self.organizacao} ({self.get_papel_display()})"


class TecnologiaProjeto(models.Model):
    """core.bridge_projeto_tecnologia. principal e mantido automaticamente
    a partir de Projeto.tecnologia_principal — nao editavel diretamente
    aqui (ver core_admin/admin/projetos.py)."""

    pk = models.CompositePrimaryKey("projeto", "tecnologia")
    projeto = models.ForeignKey(Projeto, db_column="id_projeto", on_delete=models.CASCADE, related_name="tecnologias")
    tecnologia = models.ForeignKey(
        Tecnologia, db_column="id_tecnologia", on_delete=models.RESTRICT, related_name="projetos_que_usam",
    )
    principal = models.BooleanField(default=False)
    criado_em = models.DateTimeField(editable=False)

    class Meta:
        managed = False
        db_table = '"core"."bridge_projeto_tecnologia"'
        verbose_name = "Tecnologia do projeto"
        verbose_name_plural = "Tecnologias do projeto"

    def __str__(self) -> str:
        return str(self.tecnologia)
