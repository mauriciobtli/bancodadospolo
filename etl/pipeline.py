"""Pipeline de referencia: raw.organizacoes -> core.dim_organizacao.

Implementa o fluxo completo pedido na Fase 3: validacao de CNPJ,
normalizacao de nomes, tratamento de datas, deduplicacao de organizacoes e
quarentena de registros invalidos. Os demais loaders (investimentos,
inovacoes, conexoes, etc.) seguem o mesmo padrao: ler para `raw.*` com
etl/loaders, depois transformar/validar/gravar em `core.*` com uma funcao
`processar_<entidade>` analoga a `processar_organizacoes` abaixo.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from etl.execucao import RegistroExecucao
from etl.loaders.csv_loader import carregar_csv_para_raw
from etl.transforms.datas import parse_data
from etl.transforms.dedup_organizacao import buscar_organizacao_existente
from etl.transforms.normalizacao import (
    normalizar_booleano,
    normalizar_codigo,
    normalizar_texto,
)
from etl.validators.cnpj import is_valid_cnpj, normalize_cnpj
from etl.validators.dominios import PORTE, TIPO_ORGANIZACAO, validar_dominio

MAPEAMENTO_COLUNAS_ORGANIZACOES = {
    "nome": "nome",
    "nome_fantasia": "nome_fantasia",
    "cnpj": "cnpj",
    "tipo_organizacao": "tipo_organizacao",
    "municipio": "municipio",
    "uf": "uf",
    "setor_economico": "setor_economico",
    "porte": "porte",
    "ano_fundacao": "ano_fundacao",
    "site": "site",
    "ativa": "ativa",
    "data_entrada_ecossistema": "data_entrada_ecossistema",
    "nome_contato": "nome_contato",
    "email_contato": "email_contato",
    "telefone_contato": "telefone_contato",
    "cargo_contato": "cargo_contato",
}


def carregar_organizacoes_csv(conn: Connection, caminho: Path) -> RegistroExecucao:
    return carregar_csv_para_raw(
        conn,
        caminho,
        tabela_raw="organizacoes",
        entidade_alvo="core.dim_organizacao",
        mapeamento_colunas=MAPEAMENTO_COLUNAS_ORGANIZACOES,
    )


def _resolver_municipio(conn: Connection, nome_municipio: str | None, uf: str | None) -> int | None:
    if not nome_municipio:
        return None
    row = conn.execute(
        text(
            "SELECT id_municipio FROM core.dim_municipio "
            "WHERE lower(nome) = lower(:nome) "
            "AND (CAST(:uf AS text) IS NULL OR upper(uf) = upper(CAST(:uf AS text)))"
        ),
        {"nome": nome_municipio.strip(), "uf": uf.strip() if uf else None},
    ).first()
    return row[0] if row else None


def _resolver_setor(conn: Connection, setor_economico: str | None) -> int | None:
    codigo = normalizar_codigo(setor_economico)
    if codigo is None:
        return None
    row = conn.execute(
        text("SELECT id_setor FROM core.dim_setor WHERE codigo = :codigo"),
        {"codigo": codigo},
    ).first()
    return row[0] if row else None


def processar_organizacoes(conn: Connection, execucao: RegistroExecucao) -> None:
    """Le raw.organizacoes desta execucao, valida/normaliza e grava em core."""
    linhas = conn.execute(
        text("SELECT * FROM raw.organizacoes WHERE id_execucao = :id_execucao ORDER BY linha_origem"),
        {"id_execucao": execucao.id_execucao},
    ).mappings().all()

    for linha in linhas:
        dados: dict[str, Any] = dict(linha)
        linha_origem = dados.get("linha_origem")

        nome = normalizar_texto(dados.get("nome"))
        if not nome:
            execucao.rejeitar("organizacao", linha_origem, dados, "nome ausente")
            continue

        cnpj_normalizado = normalize_cnpj(dados.get("cnpj"))
        if cnpj_normalizado is not None and not is_valid_cnpj(cnpj_normalizado):
            execucao.rejeitar("organizacao", linha_origem, dados, "cnpj_invalido")
            continue

        tipo_organizacao = normalizar_codigo(dados.get("tipo_organizacao"))
        if not validar_dominio(tipo_organizacao, TIPO_ORGANIZACAO, obrigatorio=True):
            execucao.rejeitar(
                "organizacao", linha_origem, dados,
                f"tipo_organizacao fora do dominio: {dados.get('tipo_organizacao')!r}",
            )
            continue

        porte = normalizar_codigo(dados.get("porte")) or "nao_informado"
        if not validar_dominio(porte, PORTE, obrigatorio=False):
            porte = "nao_informado"

        ano_fundacao = None
        if dados.get("ano_fundacao"):
            try:
                ano_fundacao = int(float(dados["ano_fundacao"]))
            except (TypeError, ValueError):
                execucao.rejeitar("organizacao", linha_origem, dados, "ano_fundacao invalido")
                continue

        data_entrada = parse_data(dados.get("data_entrada_ecossistema"))
        ativa = normalizar_booleano(dados.get("ativa"))
        if ativa is None:
            ativa = True

        id_municipio = _resolver_municipio(conn, dados.get("municipio"), dados.get("uf"))
        id_setor = _resolver_setor(conn, dados.get("setor_economico"))

        id_organizacao_existente = buscar_organizacao_existente(
            conn, cnpj=cnpj_normalizado, nome=nome, id_municipio=id_municipio
        )

        if id_organizacao_existente is not None:
            conn.execute(
                text(
                    """
                    UPDATE core.dim_organizacao SET
                        nome_fantasia = COALESCE(:nome_fantasia, nome_fantasia),
                        tipo_organizacao = :tipo_organizacao,
                        id_municipio = COALESCE(:id_municipio, id_municipio),
                        id_setor = COALESCE(:id_setor, id_setor),
                        porte = :porte,
                        site = COALESCE(:site, site),
                        ativa = :ativa
                    WHERE id_organizacao = :id_organizacao
                    """
                ),
                {
                    "nome_fantasia": normalizar_texto(dados.get("nome_fantasia")),
                    "tipo_organizacao": tipo_organizacao,
                    "id_municipio": id_municipio,
                    "id_setor": id_setor,
                    "porte": porte,
                    "site": normalizar_texto(dados.get("site")),
                    "ativa": ativa,
                    "id_organizacao": id_organizacao_existente,
                },
            )
            id_organizacao = id_organizacao_existente
            execucao.registros_atualizados += 1
        else:
            row = conn.execute(
                text(
                    """
                    INSERT INTO core.dim_organizacao
                        (nome, nome_fantasia, cnpj, tipo_organizacao, id_municipio, id_setor,
                         porte, ano_fundacao, site, ativa, data_entrada_ecossistema, fonte_dado)
                    VALUES
                        (:nome, :nome_fantasia, :cnpj, :tipo_organizacao, :id_municipio, :id_setor,
                         :porte, :ano_fundacao, :site, :ativa, :data_entrada_ecossistema, :fonte_dado)
                    RETURNING id_organizacao
                    """
                ),
                {
                    "nome": nome,
                    "nome_fantasia": normalizar_texto(dados.get("nome_fantasia")),
                    "cnpj": cnpj_normalizado,
                    "tipo_organizacao": tipo_organizacao,
                    "id_municipio": id_municipio,
                    "id_setor": id_setor,
                    "porte": porte,
                    "ano_fundacao": ano_fundacao,
                    "site": normalizar_texto(dados.get("site")),
                    "ativa": ativa,
                    "data_entrada_ecossistema": data_entrada,
                    "fonte_dado": dados.get("arquivo_origem") or "etl",
                },
            ).first()
            assert row is not None
            id_organizacao = row[0]
            execucao.registros_inseridos += 1

        contato_presente = any(
            dados.get(campo) for campo in ("nome_contato", "email_contato", "telefone_contato", "cargo_contato")
        )
        if contato_presente:
            conn.execute(
                text(
                    """
                    INSERT INTO core.contato_organizacao
                        (id_organizacao, nome_contato, email, telefone, cargo, fonte_dado)
                    VALUES (:id_organizacao, :nome_contato, :email, :telefone, :cargo, :fonte_dado)
                    """
                ),
                {
                    "id_organizacao": id_organizacao,
                    "nome_contato": normalizar_texto(dados.get("nome_contato")),
                    "email": normalizar_texto(dados.get("email_contato")),
                    "telefone": normalizar_texto(dados.get("telefone_contato")),
                    "cargo": normalizar_texto(dados.get("cargo_contato")),
                    "fonte_dado": dados.get("arquivo_origem") or "etl",
                },
            )
