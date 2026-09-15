"""Choices dos formularios do admin, derivadas dos MESMOS dominios usados
pelo ETL (etl/validators/dominios.py) — uma unica lista de valores validos
para cada campo, nunca duas. O Postgres continua sendo quem de fato rejeita
um valor invalido (CHECK constraint); os choices aqui so evitam que o
usuario digite algo fora do dominio na tela.
"""
from __future__ import annotations

from etl.validators import dominios as _d

_ROTULOS = {
    # organizacao
    "empresa": "Empresa", "startup": "Startup", "universidade": "Universidade",
    "ict": "ICT", "governo": "Governo", "associacao": "Associação",
    "investidor": "Investidor", "outro": "Outro",
    "mei": "MEI", "micro": "Micro", "pequena": "Pequena", "media": "Média",
    "grande": "Grande", "nao_informado": "Não informado",
    "encerramento": "Encerramento", "fusao_aquisicao": "Fusão/Aquisição",
    "saiu_area_atuacao": "Saiu da área de atuação", "inatividade": "Inatividade",
    # investimento
    "p_d": "P&D", "infraestrutura": "Infraestrutura", "software_dados": "Software/Dados",
    "capacitacao": "Capacitação", "propriedade_intelectual": "Propriedade intelectual",
    "engenharia_design": "Engenharia/Design", "outros": "Outros",
    # conexao
    "pesquisa": "Pesquisa", "parceria": "Parceria", "contrato": "Contrato",
    "mentoria": "Mentoria", "transferencia_tecnologia": "Transferência de tecnologia",
    "investimento": "Investimento", "fornecimento": "Fornecimento", "evento": "Evento",
    # projeto / papel
    "lider": "Líder", "parceiro": "Parceiro", "executor": "Executor",
    "financiador": "Financiador", "fornecedor": "Fornecedor", "beneficiario": "Beneficiário",
    "planejado": "Planejado", "em_andamento": "Em andamento", "concluido": "Concluído",
    "cancelado": "Cancelado", "suspenso": "Suspenso",
    # inovacao
    "ideacao": "Ideação", "em_desenvolvimento": "Em desenvolvimento", "piloto": "Piloto",
    "implementada": "Implementada", "descontinuada": "Descontinuada",
    "complementa": "Complementa", "substitui_parcialmente": "Substitui parcialmente",
    "substitui_predominantemente": "Substitui predominantemente", "neutro": "Neutro",
    "nao_aplicavel": "Não aplicável",
    # propriedade intelectual
    "patente": "Patente", "marca": "Marca", "registro_software": "Registro de software",
    "desenho_industrial": "Desenho industrial", "cultivar": "Cultivar",
    "depositado": "Depositado", "em_analise": "Em análise", "concedido": "Concedido",
    "indeferido": "Indeferido", "expirado": "Expirado",
    # regiao / ciclo
    "norte": "Norte", "nordeste": "Nordeste", "centro_oeste": "Centro-Oeste",
    "sudeste": "Sudeste", "sul": "Sul",
    "censitario": "Censitário", "amostral": "Amostral",
}


def _choices(dominio: set[str]) -> list[tuple[str, str]]:
    return sorted(((valor, _ROTULOS.get(valor, valor.replace("_", " ").title())) for valor in dominio), key=lambda par: par[1])


TIPO_ORGANIZACAO = _choices(_d.TIPO_ORGANIZACAO)
PORTE = _choices(_d.PORTE)
MOTIVO_SAIDA_ORGANIZACAO = _choices(_d.MOTIVO_SAIDA_ORGANIZACAO)
CATEGORIA_INVESTIMENTO = _choices(_d.CATEGORIA_INVESTIMENTO)
TIPO_CONEXAO = _choices(_d.TIPO_CONEXAO)
STATUS_PROJETO = _choices(_d.STATUS_PROJETO)
STATUS_INOVACAO = _choices(_d.STATUS_INOVACAO)
IMPACTO_TRABALHO = _choices(_d.IMPACTO_TRABALHO)
TIPO_PI = _choices(_d.TIPO_PI)
STATUS_PI = _choices(_d.STATUS_PI)
REGIAO = _choices(_d.REGIAO)
TIPO_COBERTURA_CICLO = _choices(_d.TIPO_COBERTURA_CICLO)

# Papel de projeto: o admin nunca deixa escolher 'lider' na aba de
# participantes — quem define o lider e core.projeto.id_organizacao_lider
# (ver core_admin/admin/projetos.py e o trigger de sincronizacao no banco).
PAPEL_PROJETO_TODOS = _choices(_d.PAPEL_PROJETO)
PAPEL_PROJETO_PARTICIPANTE = [par for par in PAPEL_PROJETO_TODOS if par[0] != "lider"]

NIVEL_ADOCAO = [
    (0, "0 — Não utiliza"),
    (1, "1 — Piloto"),
    (2, "2 — Uso pontual"),
    (3, "3 — Uso recorrente"),
    (4, "4 — Tecnologia crítica"),
]
