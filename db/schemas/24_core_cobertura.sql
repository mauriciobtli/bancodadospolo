-- =========================================================================
-- core: universo pesquisado e cobertura de coleta
--
-- Resolve uma ambiguidade central de qualquer pesquisa de campo: a
-- ausencia de um dado NAO significa "zero" ou "nao utiliza". Uma
-- organizacao pode estar fora do universo pesquisado num ciclo, estar no
-- universo mas nao ter respondido, ou ter respondido e declarado
-- explicitamente que nao utiliza uma tecnologia (fato_adocao_tecnologica
-- com nivel_adocao=0). Essas tres situacoes sao completamente diferentes
-- para fins de calculo de indicador e agora sao representaveis.
-- =========================================================================

-- Um ciclo de coleta = uma rodada de pesquisa/levantamento (ex.: "Pesquisa
-- Polo Inovale 2024"). Pode ser censitario (todas as organizacoes do
-- ecossistema) ou amostral (subconjunto).
CREATE TABLE IF NOT EXISTS core.ciclo_coleta (
    id_ciclo         bigserial PRIMARY KEY,
    nome             text NOT NULL,
    ano_referencia   smallint NOT NULL,
    data_inicio      date,
    data_fim         date,
    tipo_cobertura   text NOT NULL DEFAULT 'amostral',
    descricao        text,
    fonte_dado       text NOT NULL,
    criado_em        timestamptz NOT NULL DEFAULT now(),
    atualizado_em    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_ciclo_coleta_nome_ano UNIQUE (nome, ano_referencia),
    CONSTRAINT ck_ciclo_coleta_tipo CHECK (tipo_cobertura IN ('censitario', 'amostral')),
    CONSTRAINT ck_ciclo_coleta_datas CHECK (data_fim IS NULL OR data_inicio IS NULL OR data_fim >= data_inicio)
);
COMMENT ON TABLE core.ciclo_coleta IS 'Uma rodada de coleta/pesquisa (ex.: "Pesquisa Polo Inovale 2024"). Base temporal para universo_pesquisado e cobertura_coleta.';

CREATE OR REPLACE TRIGGER trg_ciclo_coleta_atualizado_em
    BEFORE UPDATE ON core.ciclo_coleta
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_ciclo_coleta_ano ON core.ciclo_coleta (ano_referencia);

-- Universo pesquisado: quais organizacoes estavam no escopo (sampling
-- frame) de um ciclo, independente de terem respondido ou nao.
CREATE TABLE IF NOT EXISTS core.universo_pesquisado (
    id_ciclo              bigint NOT NULL REFERENCES core.ciclo_coleta (id_ciclo) ON DELETE CASCADE,
    id_organizacao        bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    elegivel              boolean NOT NULL DEFAULT true,
    motivo_inelegibilidade text,
    fonte_dado            text NOT NULL,
    criado_em             timestamptz NOT NULL DEFAULT now(),
    atualizado_em         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id_ciclo, id_organizacao)
);
COMMENT ON TABLE core.universo_pesquisado IS 'Sampling frame: organizacoes dentro do escopo de um ciclo de coleta. elegivel=false registra exclusoes (ex.: organizacao encerrada antes do ciclo) sem apagar a linha.';

CREATE INDEX IF NOT EXISTS ix_universo_pesquisado_organizacao ON core.universo_pesquisado (id_organizacao);

CREATE OR REPLACE TRIGGER trg_universo_pesquisado_atualizado_em
    BEFORE UPDATE ON core.universo_pesquisado
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- Cobertura de coleta: quais organizacoes do universo efetivamente
-- responderam ao ciclo. respondeu=false e diferente de "sem linha" — um
-- registro explicito de nao-resposta permite diferenciar organizacao
-- nao-respondente de organizacao fora do escopo (sem linha em
-- universo_pesquisado) ou de organizacao que respondeu e declarou "nao
-- utiliza" (fato_adocao_tecnologica.nivel_adocao = 0).
CREATE TABLE IF NOT EXISTS core.cobertura_coleta (
    id_ciclo        bigint NOT NULL REFERENCES core.ciclo_coleta (id_ciclo) ON DELETE CASCADE,
    id_organizacao  bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    respondeu       boolean NOT NULL,
    data_resposta   date,
    instrumento     text,
    observacao      text,
    fonte_dado      text NOT NULL,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    atualizado_em   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id_ciclo, id_organizacao)
);
COMMENT ON TABLE core.cobertura_coleta IS 'Registra, por organizacao e ciclo, se houve resposta efetiva. Junto com universo_pesquisado, forma a base de "respondentes elegiveis" usada como denominador dos KPIs de cobertura (ver mart.vw_respondentes_elegiveis).';
COMMENT ON COLUMN core.cobertura_coleta.instrumento IS 'Como a resposta foi coletada: formulario, entrevista, planilha, etc.';

CREATE INDEX IF NOT EXISTS ix_cobertura_coleta_organizacao ON core.cobertura_coleta (id_organizacao);

CREATE OR REPLACE TRIGGER trg_cobertura_coleta_atualizado_em
    BEFORE UPDATE ON core.cobertura_coleta
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- Liga cada registro de adocao tecnologica ao ciclo que o produziu. Sem
-- isso, nao ha como saber com precisao a qual cobertura (universo +
-- respondentes) uma medicao de nivel_adocao pertence. Nullable por
-- enquanto (dado historico anterior a esta estrutura), mas o ETL deve
-- preencher em toda carga nova — ver mart.vw_adocao_tecnologia.
ALTER TABLE core.fato_adocao_tecnologica
    ADD COLUMN IF NOT EXISTS id_ciclo bigint REFERENCES core.ciclo_coleta (id_ciclo);

COMMENT ON COLUMN core.fato_adocao_tecnologica.id_ciclo IS 'Ciclo de coleta que originou esta medicao. Obrigatorio, na pratica, para que a organizacao entre no denominador de mart.vw_adocao_tecnologia (respondentes elegiveis do ciclo).';

CREATE INDEX IF NOT EXISTS ix_adocao_tecnologica_ciclo ON core.fato_adocao_tecnologica (id_ciclo);
