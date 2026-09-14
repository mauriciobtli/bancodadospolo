-- =========================================================================
-- mart: estrutura para analise de rede do ecossistema (secao 8)
-- Sem algoritmos avancados de grafo nesta versao — apenas agregacoes que
-- ja permitem grau, densidade, ranking de conectividade e taxas de
-- conversao. Pode alimentar bibliotecas de grafo (Python/Gephi) depois.
-- =========================================================================

-- Grau de cada organizacao (numero de conexoes, direcao ignorada) e ranking.
CREATE OR REPLACE VIEW mart.vw_rede_grau_organizacao AS
WITH ligacoes AS (
    SELECT id_organizacao_origem AS id_organizacao FROM core.fato_conexao_ecossistema
    UNION ALL
    SELECT id_organizacao_destino AS id_organizacao FROM core.fato_conexao_ecossistema
)
SELECT
    o.id_organizacao,
    o.nome,
    o.tipo_organizacao,
    count(l.id_organizacao) AS grau,
    rank() OVER (ORDER BY count(l.id_organizacao) DESC) AS ranking_conectividade
FROM core.dim_organizacao o
LEFT JOIN ligacoes l ON l.id_organizacao = o.id_organizacao
GROUP BY o.id_organizacao, o.nome, o.tipo_organizacao
ORDER BY grau DESC;
COMMENT ON VIEW mart.vw_rede_grau_organizacao IS 'Grau de cada organizacao (numero de conexoes) e ranking de conectividade — base para "organizacoes mais conectadas".';

-- Densidade da rede: conexoes existentes / conexoes possiveis (grafo dirigido).
CREATE OR REPLACE VIEW mart.vw_rede_densidade AS
WITH n AS (
    SELECT count(*) AS total_organizacoes FROM core.dim_organizacao WHERE ativa
),
m AS (
    SELECT count(*) AS total_conexoes FROM core.fato_conexao_ecossistema
)
SELECT
    n.total_organizacoes,
    m.total_conexoes,
    round(
        m.total_conexoes::numeric / NULLIF(n.total_organizacoes * (n.total_organizacoes - 1), 0), 4
    ) AS densidade_rede
FROM n, m;
COMMENT ON VIEW mart.vw_rede_densidade IS 'Densidade da rede = conexoes existentes / conexoes possiveis entre organizacoes ativas (grafo dirigido).';

-- Conexoes agregadas por par de tipo de organizacao (empresa-universidade,
-- empresa-ICT, empresa-startup, etc.) — filtrar tipo_origem/tipo_destino no Power BI.
CREATE OR REPLACE VIEW mart.vw_rede_conexoes_por_tipo AS
SELECT
    oo.tipo_organizacao AS tipo_origem,
    od.tipo_organizacao AS tipo_destino,
    c.tipo_conexao,
    count(*) AS qtd_conexoes,
    count(*) FILTER (WHERE c.gerou_projeto) AS qtd_gerou_projeto,
    count(*) FILTER (WHERE c.gerou_contrato) AS qtd_gerou_contrato,
    count(*) FILTER (WHERE c.gerou_inovacao) AS qtd_gerou_inovacao
FROM core.fato_conexao_ecossistema c
JOIN core.dim_organizacao oo ON oo.id_organizacao = c.id_organizacao_origem
JOIN core.dim_organizacao od ON od.id_organizacao = c.id_organizacao_destino
GROUP BY oo.tipo_organizacao, od.tipo_organizacao, c.tipo_conexao;
COMMENT ON VIEW mart.vw_rede_conexoes_por_tipo IS 'Conexoes agregadas por par de tipo de organizacao e tipo de conexao. Filtre tipo_origem/tipo_destino para ver empresa-universidade, empresa-ICT, empresa-startup etc.';

-- Taxas de conversao de conexao em resultado concreto.
CREATE OR REPLACE VIEW mart.vw_rede_conversao AS
SELECT
    count(*) AS total_conexoes,
    count(*) FILTER (WHERE gerou_projeto) AS qtd_gerou_projeto,
    count(*) FILTER (WHERE gerou_contrato) AS qtd_gerou_contrato,
    count(*) FILTER (WHERE gerou_inovacao) AS qtd_gerou_inovacao,
    round(100.0 * count(*) FILTER (WHERE gerou_projeto) / NULLIF(count(*), 0), 2) AS pct_gerou_projeto,
    round(100.0 * count(*) FILTER (WHERE gerou_contrato) / NULLIF(count(*), 0), 2) AS pct_gerou_contrato,
    round(100.0 * count(*) FILTER (WHERE gerou_inovacao) / NULLIF(count(*), 0), 2) AS pct_gerou_inovacao
FROM core.fato_conexao_ecossistema;
COMMENT ON VIEW mart.vw_rede_conversao IS 'Percentual de conexoes do ecossistema que se transformaram em projeto, contrato ou inovacao.';
