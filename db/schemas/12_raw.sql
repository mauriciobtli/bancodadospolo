-- =========================================================================
-- raw: pouso de dados brutos
-- Tipagem fraca (texto) de proposito: o dado chega como veio da fonte
-- (CSV/XLSX/Sheets) e so e tipado/validado na transformacao para core.
-- Toda tabela raw carrega metadados de rastreabilidade da carga.
-- =========================================================================

CREATE TABLE IF NOT EXISTS raw.organizacoes (
    id_raw                  bigserial PRIMARY KEY,
    id_execucao              bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem              integer,
    nome                      text,
    nome_fantasia             text,
    cnpj                      text,
    tipo_organizacao          text,
    municipio                 text,
    uf                        text,
    setor_economico           text,
    porte                     text,
    ano_fundacao              text,
    site                      text,
    ativa                     text,
    data_entrada_ecossistema  text,
    nome_contato              text,
    email_contato             text,
    telefone_contato          text,
    cargo_contato             text,
    arquivo_origem            text NOT NULL,
    carregado_em              timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.organizacoes IS 'Pouso bruto de cadastro de organizacoes, 1:1 com colunas tipicas de planilha de origem.';

CREATE TABLE IF NOT EXISTS raw.investimentos (
    id_raw            bigserial PRIMARY KEY,
    id_execucao        bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem        integer,
    organizacao_cnpj    text,
    organizacao_nome    text,
    data_referencia     text,
    fonte_recurso       text,
    categoria           text,
    valor               text,
    observacao          text,
    arquivo_origem      text NOT NULL,
    carregado_em        timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.investimentos IS 'Pouso bruto de lancamentos de investimento em inovacao por organizacao/periodo.';

CREATE TABLE IF NOT EXISTS raw.projetos (
    id_raw              bigserial PRIMARY KEY,
    id_execucao          bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem          integer,
    nome                  text,
    descricao             text,
    organizacao_lider_cnpj text,
    data_inicio           text,
    data_fim_prevista     text,
    data_fim_real         text,
    status                text,
    valor_total           text,
    fonte_principal       text,
    setor                 text,
    tecnologia_principal  text,
    problema_alvo         text,
    arquivo_origem        text NOT NULL,
    carregado_em          timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.projetos IS 'Pouso bruto de projetos de inovacao/P&D.';

CREATE TABLE IF NOT EXISTS raw.inovacoes (
    id_raw                          bigserial PRIMARY KEY,
    id_execucao                      bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem                      integer,
    organizacao_cnpj                  text,
    projeto_nome                      text,
    nome                              text,
    descricao                         text,
    tipo_inovacao                     text,
    grau_novidade                     text,
    problema_alvo                     text,
    data_inicio                       text,
    data_implementacao                text,
    status                            text,
    chegou_ao_mercado                 text,
    mercado_alvo                      text,
    impacto_trabalho                  text,
    receita_associada                 text,
    reducao_custo_estimada            text,
    aumento_capacidade_percentual     text,
    empregos_criados                  text,
    empregos_qualificados_criados     text,
    tecnologias                       text,
    arquivo_origem                    text NOT NULL,
    carregado_em                      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.inovacoes IS 'Pouso bruto de inovacoes. Coluna tecnologias aceita lista separada por virgula/ponto-e-virgula (expandida para a bridge no core).';

CREATE TABLE IF NOT EXISTS raw.conexoes (
    id_raw               bigserial PRIMARY KEY,
    id_execucao            bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem            integer,
    organizacao_origem_cnpj  text,
    organizacao_destino_cnpj text,
    tipo_conexao            text,
    data_inicio             text,
    data_fim                text,
    projeto_nome            text,
    valor_financeiro        text,
    gerou_projeto           text,
    gerou_contrato          text,
    gerou_inovacao          text,
    arquivo_origem          text NOT NULL,
    carregado_em            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.conexoes IS 'Pouso bruto de conexoes entre atores do ecossistema.';

CREATE TABLE IF NOT EXISTS raw.adocao_tecnologica (
    id_raw            bigserial PRIMARY KEY,
    id_execucao         bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem         integer,
    organizacao_cnpj     text,
    tecnologia           text,
    data_referencia      text,
    nivel_adocao         text,
    ano_inicio_uso       text,
    area_aplicacao       text,
    observacao           text,
    arquivo_origem       text NOT NULL,
    carregado_em         timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.adocao_tecnologica IS 'Pouso bruto de nivel de adocao tecnologica por organizacao e periodo.';

CREATE TABLE IF NOT EXISTS raw.desempenho_organizacao (
    id_raw                        bigserial PRIMARY KEY,
    id_execucao                    bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem                    integer,
    organizacao_cnpj                text,
    ano_referencia                  text,
    faturamento                     text,
    numero_empregados               text,
    numero_empregados_tecnologia    text,
    exportacoes                     text,
    receita_produtos_novos          text,
    investimento_p_d                text,
    custos_reduzidos_por_inovacao   text,
    arquivo_origem                  text NOT NULL,
    carregado_em                    timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.desempenho_organizacao IS 'Pouso bruto de indicadores anuais de desempenho por organizacao.';

CREATE TABLE IF NOT EXISTS raw.talento (
    id_raw                          bigserial PRIMARY KEY,
    id_execucao                      bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem                      integer,
    organizacao_cnpj                  text,
    ano_referencia                    text,
    pesquisadores_p_d                 text,
    mestres                           text,
    doutores                          text,
    profissionais_stem                text,
    pessoas_capacitadas               text,
    novas_contratacoes_qualificadas   text,
    arquivo_origem                    text NOT NULL,
    carregado_em                      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.talento IS 'Pouso bruto de indicadores de capital humano por organizacao e periodo.';

CREATE TABLE IF NOT EXISTS raw.propriedade_intelectual (
    id_raw                  bigserial PRIMARY KEY,
    id_execucao               bigint REFERENCES etl.etl_execucao (id_execucao),
    linha_origem               integer,
    organizacao_cnpj           text,
    projeto_nome               text,
    tipo_pi                    text,
    titulo                     text,
    numero_registro            text,
    data_deposito              text,
    data_concessao             text,
    status                     text,
    licenciada                 text,
    receita_licenciamento      text,
    arquivo_origem             text NOT NULL,
    carregado_em               timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE raw.propriedade_intelectual IS 'Pouso bruto de ativos de propriedade intelectual.';

CREATE INDEX IF NOT EXISTS ix_raw_organizacoes_execucao ON raw.organizacoes (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_investimentos_execucao ON raw.investimentos (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_projetos_execucao ON raw.projetos (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_inovacoes_execucao ON raw.inovacoes (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_conexoes_execucao ON raw.conexoes (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_adocao_execucao ON raw.adocao_tecnologica (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_desempenho_execucao ON raw.desempenho_organizacao (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_talento_execucao ON raw.talento (id_execucao);
CREATE INDEX IF NOT EXISTS ix_raw_pi_execucao ON raw.propriedade_intelectual (id_execucao);
