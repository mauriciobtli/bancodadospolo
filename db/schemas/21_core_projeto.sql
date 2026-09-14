-- =========================================================================
-- core.projeto
-- Entidade conformada: referenciada por varios fatos, mas tambem carrega
-- uma medida orcada (valor_total). O valor efetivamente investido e
-- derivado via soma de core.fato_investimento_inovacao (ver mart).
-- =========================================================================
CREATE TABLE IF NOT EXISTS core.projeto (
    id_projeto              bigserial PRIMARY KEY,
    nome                    text NOT NULL,
    descricao               text,
    id_organizacao_lider    bigint REFERENCES core.dim_organizacao (id_organizacao),
    data_inicio             date,
    data_fim_prevista       date,
    data_fim_real           date,
    status                  text NOT NULL DEFAULT 'planejado',
    valor_total             numeric(16, 2),
    id_fonte_principal      bigint REFERENCES core.dim_fonte_recurso (id_fonte_recurso),
    id_setor                bigint REFERENCES core.dim_setor (id_setor),
    id_tecnologia_principal bigint REFERENCES core.dim_tecnologia (id_tecnologia),
    id_problema_alvo        bigint REFERENCES core.dim_problema_alvo (id_problema_alvo),
    sustentabilidade        boolean,
    automacao               boolean,
    impacto_trabalho        text,
    mercado_alvo            text,
    fonte_dado              text NOT NULL,
    data_coleta             date,
    criado_em               timestamptz NOT NULL DEFAULT now(),
    atualizado_em           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_projeto_status CHECK (status IN (
        'planejado','em_andamento','concluido','cancelado','suspenso'
    )),
    CONSTRAINT ck_projeto_valor_total CHECK (valor_total IS NULL OR valor_total >= 0),
    CONSTRAINT ck_projeto_impacto_trabalho CHECK (impacto_trabalho IS NULL OR impacto_trabalho IN (
        'complementa','substitui_parcialmente','substitui_predominantemente','neutro','nao_aplicavel'
    )),
    CONSTRAINT ck_projeto_datas CHECK (
        data_fim_prevista IS NULL OR data_inicio IS NULL OR data_fim_prevista >= data_inicio
    ),
    CONSTRAINT ck_projeto_datas_real CHECK (
        data_fim_real IS NULL OR data_inicio IS NULL OR data_fim_real >= data_inicio
    )
);
COMMENT ON TABLE core.projeto IS 'Projetos de inovacao/P&D. valor_total e orcado/planejado; investimento realizado vem de core.fato_investimento_inovacao.';
COMMENT ON COLUMN core.projeto.sustentabilidade IS 'Classificacao de direcionalidade: o projeto tem foco em sustentabilidade (booleano simples nesta primeira versao).';
COMMENT ON COLUMN core.projeto.automacao IS 'Classificacao de direcionalidade: o projeto envolve automacao (booleano simples nesta primeira versao).';
COMMENT ON COLUMN core.projeto.id_organizacao_lider IS 'Fonte de verdade de quem lidera o projeto. Triggers em 23_core_bridges.sql mantem core.bridge_projeto_organizacao (papel=''lider'') sincronizada automaticamente com este campo, e bloqueiam edicao direta da bridge que divirja dele.';
COMMENT ON COLUMN core.projeto.id_tecnologia_principal IS 'Fonte de verdade da tecnologia principal do projeto. Triggers em 23_core_bridges.sql mantem core.bridge_projeto_tecnologia.principal sincronizada automaticamente com este campo, e bloqueiam edicao direta da bridge que divirja dele.';

CREATE OR REPLACE TRIGGER trg_projeto_atualizado_em
    BEFORE UPDATE ON core.projeto
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_projeto_organizacao_lider ON core.projeto (id_organizacao_lider);
CREATE INDEX IF NOT EXISTS ix_projeto_setor ON core.projeto (id_setor);
CREATE INDEX IF NOT EXISTS ix_projeto_tecnologia ON core.projeto (id_tecnologia_principal);
CREATE INDEX IF NOT EXISTS ix_projeto_fonte ON core.projeto (id_fonte_principal);
CREATE INDEX IF NOT EXISTS ix_projeto_status ON core.projeto (status);
