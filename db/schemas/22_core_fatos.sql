-- =========================================================================
-- core: tabelas fato
-- Fatos nunca sao apagados fisicamente para remover historico; correcoes
-- de um periodo ja carregado sao tratadas como upsert na chave de grao
-- (ver UNIQUE de cada tabela), preservando criado_em original e atualizando
-- atualizado_em. Um novo periodo (id_tempo diferente) sempre gera uma nova
-- linha, nunca sobrescreve o periodo anterior.
-- =========================================================================

-- --------------------------------------------- fato_investimento_inovacao
-- Grao: organizacao + periodo + fonte de recurso + categoria de investimento.
CREATE TABLE IF NOT EXISTS core.fato_investimento_inovacao (
    id_fato             bigserial PRIMARY KEY,
    id_organizacao      bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    id_tempo            bigint NOT NULL REFERENCES core.dim_tempo (id_tempo),
    id_fonte_recurso    bigint NOT NULL REFERENCES core.dim_fonte_recurso (id_fonte_recurso),
    id_projeto          bigint REFERENCES core.projeto (id_projeto),
    categoria           text NOT NULL,
    valor               numeric(16, 2) NOT NULL,
    observacao          text,
    fonte_dado          text NOT NULL,
    data_coleta         date,
    criado_em           timestamptz NOT NULL DEFAULT now(),
    atualizado_em       timestamptz NOT NULL DEFAULT now(),
    -- NULLS NOT DISTINCT (PostgreSQL 16+): id_projeto e opcional, e duas
    -- linhas com o mesmo organizacao/tempo/fonte/categoria e AMBAS sem
    -- projeto vinculado devem ser tratadas como o mesmo grao (violacao de
    -- unicidade), nao como registros distintos. Sem NULLS NOT DISTINCT, o
    -- Postgres trataria NULL <> NULL e permitiria duplicatas silenciosas
    -- sempre que id_projeto nao fosse informado.
    CONSTRAINT uq_investimento_grao UNIQUE NULLS NOT DISTINCT (
        id_organizacao, id_tempo, id_fonte_recurso, categoria, id_projeto
    ),
    CONSTRAINT ck_investimento_valor CHECK (valor >= 0),
    CONSTRAINT ck_investimento_categoria CHECK (categoria IN (
        'p_d','infraestrutura','software_dados','capacitacao',
        'propriedade_intelectual','engenharia_design','outros'
    ))
);
COMMENT ON TABLE core.fato_investimento_inovacao IS 'Investimentos em inovacao por organizacao, periodo, fonte de recurso e categoria.';
COMMENT ON COLUMN core.fato_investimento_inovacao.id_projeto IS 'Vinculo opcional ao projeto financiado. Usado pelas views mart.vw_investimento_por_tecnologia/setor para herdar a tecnologia/setor do projeto quando o investimento nao e diretamente ligado a organizacao.';
COMMENT ON COLUMN core.fato_investimento_inovacao.categoria IS
    'FONTE DE VERDADE para o detalhamento de investimento em P&D por fonte de recurso/projeto/tecnologia '
    '(categoria = ''p_d''): soma de core.fato_investimento_inovacao.valor WHERE categoria=''p_d''. '
    'E uma fonte DIFERENTE de core.fato_desempenho_organizacao.investimento_p_d (total anual '
    'autodeclarado pela organizacao) — nao devem ser somadas nem comparadas como se fossem a mesma '
    'medida. Ver comentario em fato_desempenho_organizacao.investimento_p_d e mart.vw_conciliacao_investimento_pd.';

CREATE OR REPLACE TRIGGER trg_investimento_atualizado_em
    BEFORE UPDATE ON core.fato_investimento_inovacao
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_investimento_organizacao ON core.fato_investimento_inovacao (id_organizacao);
CREATE INDEX IF NOT EXISTS ix_investimento_tempo ON core.fato_investimento_inovacao (id_tempo);
CREATE INDEX IF NOT EXISTS ix_investimento_fonte ON core.fato_investimento_inovacao (id_fonte_recurso);
CREATE INDEX IF NOT EXISTS ix_investimento_categoria ON core.fato_investimento_inovacao (categoria);
CREATE INDEX IF NOT EXISTS ix_investimento_projeto ON core.fato_investimento_inovacao (id_projeto);

-- ------------------------------------------------------------ fato_inovacao
-- Grao: uma inovacao individual.
CREATE TABLE IF NOT EXISTS core.fato_inovacao (
    id_inovacao                     bigserial PRIMARY KEY,
    id_organizacao                  bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    id_projeto                      bigint REFERENCES core.projeto (id_projeto),
    nome                            text NOT NULL,
    descricao                       text,
    id_tipo_inovacao                bigint NOT NULL REFERENCES core.dim_tipo_inovacao (id_tipo_inovacao),
    id_grau_novidade                bigint NOT NULL REFERENCES core.dim_grau_novidade (id_grau_novidade),
    id_problema_alvo                bigint REFERENCES core.dim_problema_alvo (id_problema_alvo),
    data_inicio                     date,
    data_implementacao              date,
    status                          text NOT NULL DEFAULT 'ideacao',
    chegou_ao_mercado                boolean NOT NULL DEFAULT false,
    mercado_alvo                    text,
    impacto_trabalho                text,
    receita_associada               numeric(16, 2),
    reducao_custo_estimada          numeric(16, 2),
    aumento_capacidade_percentual   numeric(6, 2),
    empregos_criados                integer NOT NULL DEFAULT 0,
    empregos_qualificados_criados   integer NOT NULL DEFAULT 0,
    id_origem_externa               text,
    fonte_dado                      text NOT NULL,
    data_coleta                     date,
    criado_em                       timestamptz NOT NULL DEFAULT now(),
    atualizado_em                   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_inovacao_status CHECK (status IN (
        'ideacao','em_desenvolvimento','piloto','implementada','descontinuada'
    )),
    CONSTRAINT ck_inovacao_impacto_trabalho CHECK (impacto_trabalho IS NULL OR impacto_trabalho IN (
        'complementa','substitui_parcialmente','substitui_predominantemente','neutro','nao_aplicavel'
    )),
    CONSTRAINT ck_inovacao_receita CHECK (receita_associada IS NULL OR receita_associada >= 0),
    CONSTRAINT ck_inovacao_reducao_custo CHECK (reducao_custo_estimada IS NULL OR reducao_custo_estimada >= 0),
    CONSTRAINT ck_inovacao_empregos CHECK (empregos_criados >= 0 AND empregos_qualificados_criados >= 0),
    CONSTRAINT ck_inovacao_empregos_qualificados CHECK (empregos_qualificados_criados <= empregos_criados),
    CONSTRAINT ck_inovacao_datas CHECK (
        data_implementacao IS NULL OR data_inicio IS NULL OR data_implementacao >= data_inicio
    )
);
COMMENT ON TABLE core.fato_inovacao IS 'Uma inovacao individual (produto, servico, processo, modelo de negocio ou tecnologia habilitadora) implementada por uma organizacao.';
COMMENT ON COLUMN core.fato_inovacao.id_origem_externa IS
    'Identificador estavel do registro na fonte (ex.: id de resposta de formulario, ou '
    '''<arquivo_origem>#<linha_origem>'' quando a fonte nao tem id proprio). Junto com o indice '
    'unico parcial abaixo, permite ao ETL fazer INSERT ... ON CONFLICT (id_origem_externa) DO '
    'UPDATE em reprocessamentos, evitando duplicar a mesma inovacao a cada nova carga do mesmo arquivo.';

CREATE OR REPLACE TRIGGER trg_inovacao_atualizado_em
    BEFORE UPDATE ON core.fato_inovacao
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_inovacao_organizacao ON core.fato_inovacao (id_organizacao);
CREATE INDEX IF NOT EXISTS ix_inovacao_projeto ON core.fato_inovacao (id_projeto);
CREATE INDEX IF NOT EXISTS ix_inovacao_tipo ON core.fato_inovacao (id_tipo_inovacao);
CREATE INDEX IF NOT EXISTS ix_inovacao_grau_novidade ON core.fato_inovacao (id_grau_novidade);
CREATE INDEX IF NOT EXISTS ix_inovacao_status ON core.fato_inovacao (status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_inovacao_origem_externa
    ON core.fato_inovacao (id_origem_externa)
    WHERE id_origem_externa IS NOT NULL;

-- --------------------------------------------------- fato_conexao_ecossistema
-- Grao: uma relacao entre dois atores do ecossistema.
CREATE TABLE IF NOT EXISTS core.fato_conexao_ecossistema (
    id_conexao              bigserial PRIMARY KEY,
    id_organizacao_origem   bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    id_organizacao_destino  bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    tipo_conexao            text NOT NULL,
    data_inicio             date,
    data_fim                date,
    id_projeto              bigint REFERENCES core.projeto (id_projeto),
    valor_financeiro        numeric(16, 2),
    gerou_projeto           boolean NOT NULL DEFAULT false,
    gerou_contrato          boolean NOT NULL DEFAULT false,
    gerou_inovacao          boolean NOT NULL DEFAULT false,
    id_origem_externa       text,
    fonte_dado              text NOT NULL,
    data_coleta             date,
    criado_em               timestamptz NOT NULL DEFAULT now(),
    atualizado_em           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_conexao_origem_destino CHECK (id_organizacao_origem <> id_organizacao_destino),
    CONSTRAINT ck_conexao_tipo CHECK (tipo_conexao IN (
        'pesquisa','parceria','contrato','mentoria','transferencia_tecnologia',
        'investimento','fornecimento','evento','outro'
    )),
    CONSTRAINT ck_conexao_valor CHECK (valor_financeiro IS NULL OR valor_financeiro >= 0),
    CONSTRAINT ck_conexao_datas CHECK (data_fim IS NULL OR data_inicio IS NULL OR data_fim >= data_inicio)
);
COMMENT ON TABLE core.fato_conexao_ecossistema IS 'Relacao dirigida entre dois atores do ecossistema (pesquisa, parceria, contrato, mentoria etc.), base para analise de rede.';
COMMENT ON COLUMN core.fato_conexao_ecossistema.id_origem_externa IS
    'Identificador estavel do registro na fonte, para permitir upsert idempotente em reprocessamentos (mesmo mecanismo de fato_inovacao.id_origem_externa).';

CREATE OR REPLACE TRIGGER trg_conexao_atualizado_em
    BEFORE UPDATE ON core.fato_conexao_ecossistema
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_conexao_origem ON core.fato_conexao_ecossistema (id_organizacao_origem);
CREATE INDEX IF NOT EXISTS ix_conexao_destino ON core.fato_conexao_ecossistema (id_organizacao_destino);
CREATE INDEX IF NOT EXISTS ix_conexao_projeto ON core.fato_conexao_ecossistema (id_projeto);
CREATE INDEX IF NOT EXISTS ix_conexao_tipo ON core.fato_conexao_ecossistema (tipo_conexao);
CREATE UNIQUE INDEX IF NOT EXISTS uq_conexao_origem_externa
    ON core.fato_conexao_ecossistema (id_origem_externa)
    WHERE id_origem_externa IS NOT NULL;

-- --------------------------------------------------- fato_adocao_tecnologica
-- Grao: organizacao + tecnologia + periodo.
CREATE TABLE IF NOT EXISTS core.fato_adocao_tecnologica (
    id_fato             bigserial PRIMARY KEY,
    id_organizacao      bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    id_tecnologia       bigint NOT NULL REFERENCES core.dim_tecnologia (id_tecnologia),
    id_tempo            bigint NOT NULL REFERENCES core.dim_tempo (id_tempo),
    nivel_adocao        smallint NOT NULL,
    ano_inicio_uso       smallint,
    area_aplicacao      text,
    observacao          text,
    fonte_dado          text NOT NULL,
    data_coleta         date,
    criado_em           timestamptz NOT NULL DEFAULT now(),
    atualizado_em       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_adocao_grao UNIQUE (id_organizacao, id_tecnologia, id_tempo),
    CONSTRAINT ck_adocao_nivel CHECK (nivel_adocao BETWEEN 0 AND 4)
);
COMMENT ON TABLE core.fato_adocao_tecnologica IS 'Nivel de adocao de cada tecnologia por organizacao e periodo. 0=nao utiliza .. 4=tecnologia critica.';

CREATE OR REPLACE TRIGGER trg_adocao_atualizado_em
    BEFORE UPDATE ON core.fato_adocao_tecnologica
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_adocao_organizacao ON core.fato_adocao_tecnologica (id_organizacao);
CREATE INDEX IF NOT EXISTS ix_adocao_tecnologia ON core.fato_adocao_tecnologica (id_tecnologia);
CREATE INDEX IF NOT EXISTS ix_adocao_tempo ON core.fato_adocao_tecnologica (id_tempo);

-- ------------------------------------------------ fato_desempenho_organizacao
-- Grao: organizacao + ano (id_tempo referencia o dia 31/12 do ano de referencia).
CREATE TABLE IF NOT EXISTS core.fato_desempenho_organizacao (
    id_fato                          bigserial PRIMARY KEY,
    id_organizacao                   bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    id_tempo                         bigint NOT NULL REFERENCES core.dim_tempo (id_tempo),
    faturamento                      numeric(18, 2),
    numero_empregados                integer,
    numero_empregados_tecnologia     integer,
    exportacoes                      numeric(18, 2),
    receita_produtos_novos           numeric(18, 2),
    investimento_p_d                 numeric(18, 2),
    custos_reduzidos_por_inovacao    numeric(18, 2),
    fonte_dado                       text NOT NULL,
    data_coleta                      date,
    criado_em                        timestamptz NOT NULL DEFAULT now(),
    atualizado_em                    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_desempenho_grao UNIQUE (id_organizacao, id_tempo),
    CONSTRAINT ck_desempenho_faturamento CHECK (faturamento IS NULL OR faturamento >= 0),
    CONSTRAINT ck_desempenho_empregados CHECK (numero_empregados IS NULL OR numero_empregados >= 0),
    CONSTRAINT ck_desempenho_empregados_tec CHECK (
        numero_empregados_tecnologia IS NULL OR numero_empregados_tecnologia >= 0
    ),
    CONSTRAINT ck_desempenho_empregados_tec_max CHECK (
        numero_empregados_tecnologia IS NULL OR numero_empregados IS NULL
        OR numero_empregados_tecnologia <= numero_empregados
    ),
    CONSTRAINT ck_desempenho_exportacoes CHECK (exportacoes IS NULL OR exportacoes >= 0),
    CONSTRAINT ck_desempenho_receita_novos CHECK (receita_produtos_novos IS NULL OR receita_produtos_novos >= 0),
    CONSTRAINT ck_desempenho_investimento_pd CHECK (investimento_p_d IS NULL OR investimento_p_d >= 0),
    CONSTRAINT ck_desempenho_custos_reduzidos CHECK (
        custos_reduzidos_por_inovacao IS NULL OR custos_reduzidos_por_inovacao >= 0
    )
);
COMMENT ON TABLE core.fato_desempenho_organizacao IS 'Indicadores anuais de desempenho economico-financeiro por organizacao. Nunca atualiza um ano fechado com valor de outro ano.';
COMMENT ON COLUMN core.fato_desempenho_organizacao.investimento_p_d IS
    'FONTE DE VERDADE para o KPI "intensidade de P&D" (mart.vw_intensidade_p_d = '
    'investimento_p_d / faturamento), por ser autodeclarado no MESMO grao e pela MESMA fonte que '
    'o faturamento (evita comparar numerador e denominador de levantamentos diferentes). '
    'E um total anual autodeclarado, podendo divergir da soma categorizada em '
    'core.fato_investimento_inovacao (categoria=''p_d''), que e mais granular (por fonte de '
    'recurso/projeto) mas pode estar incompleta se nem todo investimento foi lancado por categoria. '
    'As duas metricas NUNCA devem ser somadas entre si; para investigar divergencias, use '
    'mart.vw_conciliacao_investimento_pd.';

CREATE OR REPLACE TRIGGER trg_desempenho_atualizado_em
    BEFORE UPDATE ON core.fato_desempenho_organizacao
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_desempenho_organizacao ON core.fato_desempenho_organizacao (id_organizacao);
CREATE INDEX IF NOT EXISTS ix_desempenho_tempo ON core.fato_desempenho_organizacao (id_tempo);

-- ------------------------------------------------------------- fato_talento
-- Grao: organizacao + periodo.
CREATE TABLE IF NOT EXISTS core.fato_talento (
    id_fato                          bigserial PRIMARY KEY,
    id_organizacao                   bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    id_tempo                         bigint NOT NULL REFERENCES core.dim_tempo (id_tempo),
    pesquisadores_p_d                integer NOT NULL DEFAULT 0,
    mestres                          integer NOT NULL DEFAULT 0,
    doutores                         integer NOT NULL DEFAULT 0,
    profissionais_stem               integer NOT NULL DEFAULT 0,
    pessoas_capacitadas              integer NOT NULL DEFAULT 0,
    novas_contratacoes_qualificadas  integer NOT NULL DEFAULT 0,
    fonte_dado                       text NOT NULL,
    data_coleta                      date,
    criado_em                        timestamptz NOT NULL DEFAULT now(),
    atualizado_em                    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_talento_grao UNIQUE (id_organizacao, id_tempo),
    CONSTRAINT ck_talento_nao_negativo CHECK (
        pesquisadores_p_d >= 0 AND mestres >= 0 AND doutores >= 0 AND
        profissionais_stem >= 0 AND pessoas_capacitadas >= 0 AND
        novas_contratacoes_qualificadas >= 0
    )
);
COMMENT ON TABLE core.fato_talento IS 'Capital humano e conhecimento por organizacao e periodo (pesquisadores, mestres, doutores, STEM).';

CREATE OR REPLACE TRIGGER trg_talento_atualizado_em
    BEFORE UPDATE ON core.fato_talento
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_talento_organizacao ON core.fato_talento (id_organizacao);
CREATE INDEX IF NOT EXISTS ix_talento_tempo ON core.fato_talento (id_tempo);

-- ----------------------------------------------- fato_propriedade_intelectual
CREATE TABLE IF NOT EXISTS core.fato_propriedade_intelectual (
    id_pi                   bigserial PRIMARY KEY,
    id_organizacao          bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    id_projeto              bigint REFERENCES core.projeto (id_projeto),
    tipo_pi                 text NOT NULL,
    titulo                  text NOT NULL,
    numero_registro         text,
    data_deposito           date,
    data_concessao          date,
    status                  text NOT NULL DEFAULT 'depositado',
    licenciada               boolean NOT NULL DEFAULT false,
    receita_licenciamento   numeric(16, 2),
    id_origem_externa       text,
    fonte_dado              text NOT NULL,
    data_coleta             date,
    criado_em               timestamptz NOT NULL DEFAULT now(),
    atualizado_em           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_pi_tipo CHECK (tipo_pi IN (
        'patente','marca','registro_software','desenho_industrial','cultivar','outro'
    )),
    CONSTRAINT ck_pi_status CHECK (status IN (
        'depositado','em_analise','concedido','indeferido','expirado'
    )),
    CONSTRAINT ck_pi_receita CHECK (receita_licenciamento IS NULL OR receita_licenciamento >= 0),
    CONSTRAINT ck_pi_datas CHECK (
        data_concessao IS NULL OR data_deposito IS NULL OR data_concessao >= data_deposito
    )
);
COMMENT ON TABLE core.fato_propriedade_intelectual IS 'Ativos de propriedade intelectual (patentes, marcas, software, cultivares) gerados pelas organizacoes.';
COMMENT ON COLUMN core.fato_propriedade_intelectual.id_origem_externa IS
    'Identificador estavel do registro na fonte (ex.: numero_registro quando existir, ou o mesmo padrao de fato_inovacao.id_origem_externa), para upsert idempotente em reprocessamentos.';

CREATE OR REPLACE TRIGGER trg_pi_atualizado_em
    BEFORE UPDATE ON core.fato_propriedade_intelectual
    FOR EACH ROW EXECUTE FUNCTION core.fn_atualizado_em();

CREATE INDEX IF NOT EXISTS ix_pi_organizacao ON core.fato_propriedade_intelectual (id_organizacao);
CREATE INDEX IF NOT EXISTS ix_pi_projeto ON core.fato_propriedade_intelectual (id_projeto);
CREATE INDEX IF NOT EXISTS ix_pi_status ON core.fato_propriedade_intelectual (status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pi_origem_externa
    ON core.fato_propriedade_intelectual (id_origem_externa)
    WHERE id_origem_externa IS NOT NULL;
