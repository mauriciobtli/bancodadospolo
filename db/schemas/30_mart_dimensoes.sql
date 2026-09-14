-- =========================================================================
-- mart: dimensoes (views de leitura sobre core, sem PII)
-- =========================================================================

CREATE OR REPLACE VIEW mart.dim_tempo AS
SELECT id_tempo, data, dia, mes, nome_mes, trimestre, ano
FROM core.dim_tempo;
COMMENT ON VIEW mart.dim_tempo IS 'Dimensao calendario (grao diario) para uso no Power BI.';

CREATE OR REPLACE VIEW mart.dim_municipio AS
SELECT id_municipio, codigo_ibge, nome, uf, regiao, pertence_area_atuacao
FROM core.dim_municipio;
COMMENT ON VIEW mart.dim_municipio IS 'Municipios de referencia e area de atuacao do Polo Inovale.';

CREATE OR REPLACE VIEW mart.dim_setor AS
SELECT id_setor, codigo, nome, descricao
FROM core.dim_setor;

CREATE OR REPLACE VIEW mart.dim_tecnologia AS
SELECT id_tecnologia, codigo, nome, descricao
FROM core.dim_tecnologia;

CREATE OR REPLACE VIEW mart.dim_tipo_inovacao AS
SELECT id_tipo_inovacao, codigo, nome
FROM core.dim_tipo_inovacao;

CREATE OR REPLACE VIEW mart.dim_grau_novidade AS
SELECT id_grau_novidade, codigo, nome, ordem
FROM core.dim_grau_novidade;

CREATE OR REPLACE VIEW mart.dim_fonte_recurso AS
SELECT id_fonte_recurso, codigo, nome
FROM core.dim_fonte_recurso;

CREATE OR REPLACE VIEW mart.dim_problema_alvo AS
SELECT id_problema_alvo, codigo, nome
FROM core.dim_problema_alvo;

-- Apenas dados publicos/institucionais. Dados pessoais de contato ficam em
-- core.contato_organizacao e NAO tem view equivalente em mart.
CREATE OR REPLACE VIEW mart.dim_organizacao AS
SELECT
    o.id_organizacao,
    o.nome,
    o.nome_fantasia,
    o.cnpj,
    o.tipo_organizacao,
    o.id_municipio,
    m.nome AS municipio_nome,
    m.uf,
    o.id_setor,
    s.nome AS setor_nome,
    o.porte,
    o.ano_fundacao,
    o.site,
    o.ativa,
    o.data_entrada_ecossistema,
    o.data_saida_ecossistema,
    o.motivo_saida
FROM core.dim_organizacao o
LEFT JOIN core.dim_municipio m ON m.id_municipio = o.id_municipio
LEFT JOIN core.dim_setor s ON s.id_setor = o.id_setor;
COMMENT ON VIEW mart.dim_organizacao IS 'Organizacoes do ecossistema, apenas dados publicos/institucionais (sem contato pessoal).';

CREATE OR REPLACE VIEW mart.dim_projeto AS
SELECT
    p.id_projeto,
    p.nome,
    p.descricao,
    p.id_organizacao_lider,
    ol.nome AS organizacao_lider_nome,
    p.data_inicio,
    p.data_fim_prevista,
    p.data_fim_real,
    p.status,
    p.valor_total,
    p.id_fonte_principal,
    fr.nome AS fonte_principal_nome,
    p.id_setor,
    s.nome AS setor_nome,
    p.id_tecnologia_principal,
    t.nome AS tecnologia_principal_nome,
    p.id_problema_alvo,
    pa.nome AS problema_alvo_nome,
    p.sustentabilidade,
    p.automacao,
    p.impacto_trabalho,
    p.mercado_alvo
FROM core.projeto p
LEFT JOIN core.dim_organizacao ol ON ol.id_organizacao = p.id_organizacao_lider
LEFT JOIN core.dim_fonte_recurso fr ON fr.id_fonte_recurso = p.id_fonte_principal
LEFT JOIN core.dim_setor s ON s.id_setor = p.id_setor
LEFT JOIN core.dim_tecnologia t ON t.id_tecnologia = p.id_tecnologia_principal
LEFT JOIN core.dim_problema_alvo pa ON pa.id_problema_alvo = p.id_problema_alvo;
COMMENT ON VIEW mart.dim_projeto IS 'Projetos com nomes de dimensoes relacionadas ja resolvidos, para simplificar o modelo consumido pelo Power BI.';

-- =========================================================================
-- Universo pesquisado / cobertura de coleta
-- =========================================================================

CREATE OR REPLACE VIEW mart.dim_ciclo_coleta AS
SELECT id_ciclo, nome, ano_referencia, data_inicio, data_fim, tipo_cobertura, descricao
FROM core.ciclo_coleta;
COMMENT ON VIEW mart.dim_ciclo_coleta IS 'Rodadas de coleta/pesquisa (ex.: "Pesquisa Polo Inovale 2024").';

CREATE OR REPLACE VIEW mart.universo_pesquisado AS
SELECT
    up.id_ciclo,
    up.id_organizacao,
    o.nome AS organizacao_nome,
    up.elegivel,
    up.motivo_inelegibilidade
FROM core.universo_pesquisado up
JOIN core.dim_organizacao o ON o.id_organizacao = up.id_organizacao;
COMMENT ON VIEW mart.universo_pesquisado IS 'Sampling frame de cada ciclo de coleta: organizacoes dentro do escopo, elegiveis ou nao.';

CREATE OR REPLACE VIEW mart.cobertura_coleta AS
SELECT
    cc.id_ciclo,
    cc.id_organizacao,
    o.nome AS organizacao_nome,
    cc.respondeu,
    cc.data_resposta,
    cc.instrumento
FROM core.cobertura_coleta cc
JOIN core.dim_organizacao o ON o.id_organizacao = cc.id_organizacao;
COMMENT ON VIEW mart.cobertura_coleta IS 'Quem efetivamente respondeu (ou nao) a cada ciclo de coleta.';

-- Respondentes elegiveis: organizacoes no universo pesquisado (elegivel)
-- E que responderam ao ciclo. Base do denominador de mart.vw_taxa_empresas_inovadoras,
-- mart.vw_taxa_primeira_inovacao e mart.vw_adocao_tecnologia — substitui o uso de
-- "todas as organizacoes ativas" ou de fato_desempenho_organizacao como proxy.
CREATE OR REPLACE VIEW mart.vw_respondentes_elegiveis AS
SELECT
    cc.id_ciclo,
    c.ano_referencia AS ano,
    cc.id_organizacao
FROM core.cobertura_coleta cc
JOIN core.universo_pesquisado up
    ON up.id_ciclo = cc.id_ciclo AND up.id_organizacao = cc.id_organizacao
JOIN core.ciclo_coleta c ON c.id_ciclo = cc.id_ciclo
WHERE cc.respondeu AND up.elegivel;
COMMENT ON VIEW mart.vw_respondentes_elegiveis IS 'Organizacoes elegiveis (universo_pesquisado) que efetivamente responderam (cobertura_coleta) em cada ciclo — base do denominador dos KPIs de cobertura.';
