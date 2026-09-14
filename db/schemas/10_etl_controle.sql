-- =========================================================================
-- etl: controle de execucao de cargas e quarentena
-- Schema de administracao — NUNCA recebe grant para a role de leitura do
-- Power BI (pode conter caminhos de arquivo, mensagens de erro internas).
-- =========================================================================

CREATE TABLE IF NOT EXISTS etl.etl_execucao (
    id_execucao         bigserial PRIMARY KEY,
    arquivo_fonte       text NOT NULL,
    tipo_fonte          text NOT NULL,
    entidade_alvo       text NOT NULL,
    iniciado_em         timestamptz NOT NULL DEFAULT now(),
    finalizado_em       timestamptz,
    registros_lidos     integer NOT NULL DEFAULT 0,
    registros_inseridos integer NOT NULL DEFAULT 0,
    registros_atualizados integer NOT NULL DEFAULT 0,
    registros_rejeitados  integer NOT NULL DEFAULT 0,
    status              text NOT NULL DEFAULT 'em_execucao',
    mensagem_erro       text,
    CONSTRAINT ck_etl_execucao_tipo_fonte CHECK (tipo_fonte IN ('csv','xlsx','google_sheets','manual')),
    CONSTRAINT ck_etl_execucao_status CHECK (status IN (
        'em_execucao','sucesso','sucesso_parcial','falha'
    )),
    CONSTRAINT ck_etl_execucao_contadores CHECK (
        registros_lidos >= 0 AND registros_inseridos >= 0 AND
        registros_atualizados >= 0 AND registros_rejeitados >= 0
    )
);
COMMENT ON TABLE etl.etl_execucao IS 'Log de cada execucao de carga do ETL: arquivo/fonte, janela de tempo, contadores e erro, se houver.';

CREATE INDEX IF NOT EXISTS ix_etl_execucao_entidade ON etl.etl_execucao (entidade_alvo);
CREATE INDEX IF NOT EXISTS ix_etl_execucao_status ON etl.etl_execucao (status);
CREATE INDEX IF NOT EXISTS ix_etl_execucao_iniciado_em ON etl.etl_execucao (iniciado_em);

CREATE TABLE IF NOT EXISTS etl.quarentena_registro (
    id_quarentena       bigserial PRIMARY KEY,
    id_execucao         bigint NOT NULL REFERENCES etl.etl_execucao (id_execucao) ON DELETE CASCADE,
    entidade             text NOT NULL,
    linha_origem         integer,
    dados_originais      jsonb NOT NULL,
    motivo_rejeicao      text NOT NULL,
    resolvido            boolean NOT NULL DEFAULT false,
    resolvido_em         timestamptz,
    criado_em            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE etl.quarentena_registro IS 'Registros rejeitados na carga (falha de validacao, CNPJ invalido, dominio fora do esperado etc.), preservados como JSON para correcao manual.';

CREATE INDEX IF NOT EXISTS ix_quarentena_execucao ON etl.quarentena_registro (id_execucao);
CREATE INDEX IF NOT EXISTS ix_quarentena_entidade ON etl.quarentena_registro (entidade);
CREATE INDEX IF NOT EXISTS ix_quarentena_resolvido ON etl.quarentena_registro (resolvido);
