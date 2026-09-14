"""Registro de execucoes de carga (etl.etl_execucao) e quarentena
(etl.quarentena_registro) — tabela `etl_execucao` pedida no briefing."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Connection


@dataclass
class RegistroExecucao:
    id_execucao: int
    conn: Connection
    registros_lidos: int = 0
    registros_inseridos: int = 0
    registros_atualizados: int = 0
    registros_rejeitados: int = 0
    _rejeicoes: list[tuple[str, int | None, dict, str]] = field(default_factory=list)

    def rejeitar(self, entidade: str, linha_origem: int | None, dados_originais: dict, motivo: str) -> None:
        self.registros_rejeitados += 1
        self._rejeicoes.append((entidade, linha_origem, dados_originais, motivo))

    def _persistir_quarentena(self) -> None:
        for entidade, linha_origem, dados_originais, motivo in self._rejeicoes:
            self.conn.execute(
                text(
                    """
                    INSERT INTO etl.quarentena_registro
                        (id_execucao, entidade, linha_origem, dados_originais, motivo_rejeicao)
                    VALUES (:id_execucao, :entidade, :linha_origem, CAST(:dados_originais AS jsonb), :motivo)
                    """
                ),
                {
                    "id_execucao": self.id_execucao,
                    "entidade": entidade,
                    "linha_origem": linha_origem,
                    "dados_originais": json.dumps(dados_originais, default=str, ensure_ascii=False),
                    "motivo": motivo,
                },
            )

    def finalizar(self, status: str, mensagem_erro: str | None = None) -> None:
        self._persistir_quarentena()
        self.conn.execute(
            text(
                """
                UPDATE etl.etl_execucao
                SET finalizado_em = now(),
                    registros_lidos = :lidos,
                    registros_inseridos = :inseridos,
                    registros_atualizados = :atualizados,
                    registros_rejeitados = :rejeitados,
                    status = :status,
                    mensagem_erro = :mensagem_erro
                WHERE id_execucao = :id_execucao
                """
            ),
            {
                "lidos": self.registros_lidos,
                "inseridos": self.registros_inseridos,
                "atualizados": self.registros_atualizados,
                "rejeitados": self.registros_rejeitados,
                "status": status,
                "mensagem_erro": mensagem_erro,
                "id_execucao": self.id_execucao,
            },
        )


def iniciar_execucao(conn: Connection, arquivo_fonte: str, tipo_fonte: str, entidade_alvo: str) -> RegistroExecucao:
    row = conn.execute(
        text(
            """
            INSERT INTO etl.etl_execucao (arquivo_fonte, tipo_fonte, entidade_alvo, status)
            VALUES (:arquivo_fonte, :tipo_fonte, :entidade_alvo, 'em_execucao')
            RETURNING id_execucao
            """
        ),
        {"arquivo_fonte": arquivo_fonte, "tipo_fonte": tipo_fonte, "entidade_alvo": entidade_alvo},
    ).first()
    assert row is not None
    return RegistroExecucao(id_execucao=row[0], conn=conn)
