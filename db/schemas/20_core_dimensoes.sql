-- =========================================================================
-- core: dimensoes
-- =========================================================================

-- ---------------------------------------------------------------- dim_tempo
CREATE TABLE IF NOT EXISTS core.dim_tempo (
    id_tempo    bigint PRIMARY KEY,
    data        date NOT NULL UNIQUE,
    dia         smallint NOT NULL,
    mes         smallint NOT NULL,
    nome_mes    text NOT NULL,
    trimestre   smallint NOT NULL,
    ano         smallint NOT NULL,
    criado_em   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.dim_tempo IS 'Dimensao calendario, grao diario. id_tempo = AAAAMMDD, populada via seed (generate_series).';

-- ----------------------------------------------------------- dim_municipio
CREATE TABLE IF NOT EXISTS core.dim_municipio (
    id_municipio            bigserial PRIMARY KEY,
    codigo_ibge             varchar(7) NOT NULL UNIQUE,
    nome                    text NOT NULL,
    uf                      char(2) NOT NULL,
    regiao                  text NOT NULL,
    pertence_area_atuacao   boolean NOT NULL DEFAULT false,
    fonte_dado              text NOT NULL DEFAULT 'seed',
    data_coleta             date,
    criado_em               timestamptz NOT NULL DEFAULT now(),
    atualizado_em           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_municipio_uf CHECK (uf ~ '^[A-Z]{2}$'),
    CONSTRAINT ck_municipio_regiao CHECK (regiao IN ('norte','nordeste','centro_oeste','sudeste','sul'))
);
COMMENT ON TABLE core.dim_municipio IS 'Municipios de referencia. pertence_area_atuacao marca os municipios cobertos pelo Polo Inovale.';

CREATE OR REPLACE TRIGGER trg_municipio_atualizado_em
    BEFORE UPDATE ON core.dim_municipio
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- --------------------------------------------------------------- dim_setor
CREATE TABLE IF NOT EXISTS core.dim_setor (
    id_setor        bigserial PRIMARY KEY,
    codigo          text NOT NULL UNIQUE,
    nome            text NOT NULL,
    descricao       text,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    atualizado_em   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.dim_setor IS 'Setores economicos das organizacoes e projetos.';

CREATE OR REPLACE TRIGGER trg_setor_atualizado_em
    BEFORE UPDATE ON core.dim_setor
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- ---------------------------------------------------------- dim_tecnologia
CREATE TABLE IF NOT EXISTS core.dim_tecnologia (
    id_tecnologia   bigserial PRIMARY KEY,
    codigo          text NOT NULL UNIQUE,
    nome            text NOT NULL,
    descricao       text,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    atualizado_em   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.dim_tecnologia IS 'Catalogo de tecnologias habilitadoras (IA, IoT, biotecnologia, etc.).';

CREATE OR REPLACE TRIGGER trg_tecnologia_atualizado_em
    BEFORE UPDATE ON core.dim_tecnologia
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- ------------------------------------------------------- dim_tipo_inovacao
CREATE TABLE IF NOT EXISTS core.dim_tipo_inovacao (
    id_tipo_inovacao   bigserial PRIMARY KEY,
    codigo              text NOT NULL UNIQUE,
    nome                text NOT NULL,
    criado_em           timestamptz NOT NULL DEFAULT now(),
    atualizado_em       timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.dim_tipo_inovacao IS 'Categoria da inovacao: produto, servico, processo, modelo de negocio, tecnologia habilitadora.';

CREATE OR REPLACE TRIGGER trg_tipo_inovacao_atualizado_em
    BEFORE UPDATE ON core.dim_tipo_inovacao
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- ------------------------------------------------------- dim_grau_novidade
CREATE TABLE IF NOT EXISTS core.dim_grau_novidade (
    id_grau_novidade   bigserial PRIMARY KEY,
    codigo              text NOT NULL UNIQUE,
    nome                text NOT NULL,
    ordem               smallint NOT NULL UNIQUE,
    criado_em           timestamptz NOT NULL DEFAULT now(),
    atualizado_em       timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.dim_grau_novidade IS 'Escala ordinal de novidade da inovacao (1=empresa .. 4=mundial). Coluna ordem permite comparacoes >=/<=.';

CREATE OR REPLACE TRIGGER trg_grau_novidade_atualizado_em
    BEFORE UPDATE ON core.dim_grau_novidade
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- ------------------------------------------------------- dim_fonte_recurso
CREATE TABLE IF NOT EXISTS core.dim_fonte_recurso (
    id_fonte_recurso   bigserial PRIMARY KEY,
    codigo              text NOT NULL UNIQUE,
    nome                text NOT NULL,
    criado_em           timestamptz NOT NULL DEFAULT now(),
    atualizado_em       timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.dim_fonte_recurso IS 'Origem do recurso financeiro (proprio, fapesc, finep, investidor, etc.).';

CREATE OR REPLACE TRIGGER trg_fonte_recurso_atualizado_em
    BEFORE UPDATE ON core.dim_fonte_recurso
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- ------------------------------------------------------- dim_problema_alvo
CREATE TABLE IF NOT EXISTS core.dim_problema_alvo (
    id_problema_alvo   bigserial PRIMARY KEY,
    codigo               text NOT NULL UNIQUE,
    nome                 text NOT NULL,
    criado_em            timestamptz NOT NULL DEFAULT now(),
    atualizado_em        timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.dim_problema_alvo IS 'Problema de negocio que a inovacao/projeto busca resolver (produtividade, custo, escassez de mao de obra, etc.).';

CREATE OR REPLACE TRIGGER trg_problema_alvo_atualizado_em
    BEFORE UPDATE ON core.dim_problema_alvo
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

-- ----------------------------------------------------------------------
-- dim_organizacao
-- Dados publicos/institucionais (nome, CNPJ, site). Dados pessoais de
-- contato (nome de pessoa, e-mail, telefone) NAO entram aqui — vivem em
-- core.contato_organizacao, fora do schema mart, para isolar PII do
-- dado analitico consumido pelo Power BI.
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.dim_organizacao (
    id_organizacao          bigserial PRIMARY KEY,
    nome                    text NOT NULL,
    nome_fantasia           text,
    cnpj                    varchar(14),
    tipo_organizacao        text NOT NULL,
    id_municipio            bigint REFERENCES core.dim_municipio (id_municipio),
    id_setor                bigint REFERENCES core.dim_setor (id_setor),
    porte                   text NOT NULL DEFAULT 'nao_informado',
    ano_fundacao            smallint,
    site                    text,
    ativa                   boolean NOT NULL DEFAULT true,
    data_entrada_ecossistema date,
    fonte_dado              text NOT NULL,
    data_coleta             date,
    criado_em               timestamptz NOT NULL DEFAULT now(),
    atualizado_em           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_organizacao_cnpj UNIQUE (cnpj),
    CONSTRAINT ck_organizacao_cnpj_formato CHECK (cnpj IS NULL OR cnpj ~ '^[0-9]{14}$'),
    CONSTRAINT ck_organizacao_tipo CHECK (tipo_organizacao IN (
        'empresa','startup','universidade','ict','governo','associacao','investidor','outro'
    )),
    CONSTRAINT ck_organizacao_porte CHECK (porte IN (
        'mei','micro','pequena','media','grande','nao_informado'
    )),
    CONSTRAINT ck_organizacao_ano_fundacao CHECK (
        ano_fundacao IS NULL OR ano_fundacao BETWEEN 1500 AND EXTRACT(YEAR FROM now())::int + 1
    )
);
COMMENT ON TABLE core.dim_organizacao IS 'Empresas, startups, universidades, ICTs, governo, associacoes etc. Apenas dados publicos/institucionais.';
COMMENT ON COLUMN core.dim_organizacao.cnpj IS 'Somente digitos (14), validado por ck_organizacao_cnpj_formato e pelo validador de digito verificador no ETL. Nulo permitido para entidades sem CNPJ (coletivos, grupos de pesquisa).';

CREATE OR REPLACE TRIGGER trg_organizacao_atualizado_em
    BEFORE UPDATE ON core.dim_organizacao
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_organizacao_municipio ON core.dim_organizacao (id_municipio);
CREATE INDEX IF NOT EXISTS ix_organizacao_setor ON core.dim_organizacao (id_setor);
CREATE INDEX IF NOT EXISTS ix_organizacao_tipo ON core.dim_organizacao (tipo_organizacao);
CREATE INDEX IF NOT EXISTS ix_organizacao_ativa ON core.dim_organizacao (ativa);

-- ----------------------------------------------------------------------
-- core.contato_organizacao
-- Dados pessoais (LGPD). Isolado em tabela propria, SEM view equivalente
-- em mart e SEM grant para a role de leitura do Power BI.
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.contato_organizacao (
    id_contato      bigserial PRIMARY KEY,
    id_organizacao  bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao) ON DELETE CASCADE,
    nome_contato    text,
    email           text,
    telefone        text,
    cargo           text,
    fonte_dado      text NOT NULL,
    data_coleta     date,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    atualizado_em   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE core.contato_organizacao IS 'Dados pessoais de contato (LGPD). Nunca exposto em mart nem para a role powerbi_readonly.';

CREATE OR REPLACE TRIGGER trg_contato_atualizado_em
    BEFORE UPDATE ON core.contato_organizacao
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_contato_organizacao ON core.contato_organizacao (id_organizacao);
