"""Dominios validos (enums) espelhando os CHECK constraints do banco.

Mantidos em Python para permitir rejeitar (quarentena) um registro no ETL
antes mesmo de tentar o INSERT, com uma mensagem de erro mais clara do que
a exception crua do Postgres.
"""
from __future__ import annotations

TIPO_ORGANIZACAO = {
    "empresa", "startup", "universidade", "ict", "governo", "associacao", "investidor", "outro",
}

PORTE = {"mei", "micro", "pequena", "media", "grande", "nao_informado"}

CATEGORIA_INVESTIMENTO = {
    "p_d", "infraestrutura", "software_dados", "capacitacao",
    "propriedade_intelectual", "engenharia_design", "outros",
}

TIPO_CONEXAO = {
    "pesquisa", "parceria", "contrato", "mentoria", "transferencia_tecnologia",
    "investimento", "fornecimento", "evento", "outro",
}

STATUS_PROJETO = {"planejado", "em_andamento", "concluido", "cancelado", "suspenso"}

STATUS_INOVACAO = {"ideacao", "em_desenvolvimento", "piloto", "implementada", "descontinuada"}

IMPACTO_TRABALHO = {
    "complementa", "substitui_parcialmente", "substitui_predominantemente", "neutro", "nao_aplicavel",
}

TIPO_PI = {"patente", "marca", "registro_software", "desenho_industrial", "cultivar", "outro"}

STATUS_PI = {"depositado", "em_analise", "concedido", "indeferido", "expirado"}

REGIAO = {"norte", "nordeste", "centro_oeste", "sudeste", "sul"}

MOTIVO_SAIDA_ORGANIZACAO = {
    "encerramento", "fusao_aquisicao", "saiu_area_atuacao", "inatividade", "outro",
}

PAPEL_PROJETO = {
    "lider", "parceiro", "executor", "financiador", "fornecedor", "beneficiario", "outro",
}

TIPO_COBERTURA_CICLO = {"censitario", "amostral"}


def validar_dominio(valor: str | None, dominio: set[str], obrigatorio: bool = True) -> bool:
    """Retorna True se o valor (normalizado) pertence ao dominio permitido."""
    if valor is None or valor == "":
        return not obrigatorio
    return valor in dominio
