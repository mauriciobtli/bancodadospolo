-- =========================================================================
-- mart: views de apoio direto as 10 areas de consumo do Power BI (secao 11)
-- Onde uma area e coberta integralmente por uma view ja existente (KPI ou
-- rede), criamos aqui um alias vw_bi_* para facilitar a navegacao no
-- catalogo do Power BI sem duplicar logica.
-- =========================================================================

-- 1) Visao executiva: principais indicadores agregados por ano.
CREATE OR REPLACE VIEW mart.vw_bi_visao_executiva AS
WITH organizacoes_ano AS (
    SELECT dt.ano, count(DISTINCT f.id_organizacao) AS empresas_acompanhadas
    FROM core.fato_desempenho_organizacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
    GROUP BY dt.ano
),
investimento_ano AS (
    SELECT dt.ano, sum(f.valor) AS investimento_total
    FROM core.fato_investimento_inovacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
    GROUP BY dt.ano
),
inovacoes_ano AS (
    SELECT extract(year FROM data_implementacao)::smallint AS ano, count(*) AS inovacoes_implementadas
    FROM core.fato_inovacao
    WHERE status = 'implementada' AND data_implementacao IS NOT NULL
    GROUP BY 1
),
projetos_ano AS (
    SELECT extract(year FROM data_fim_real)::smallint AS ano, count(*) AS projetos_concluidos
    FROM core.projeto
    WHERE status = 'concluido' AND data_fim_real IS NOT NULL
    GROUP BY 1
)
SELECT
    coalesce(o.ano, i.ano, n.ano, p.ano) AS ano,
    o.empresas_acompanhadas,
    i.investimento_total,
    n.inovacoes_implementadas,
    p.projetos_concluidos,
    round(i.investimento_total / NULLIF(n.inovacoes_implementadas, 0), 2) AS investimento_medio_por_inovacao
FROM organizacoes_ano o
FULL OUTER JOIN investimento_ano i ON i.ano = o.ano
FULL OUTER JOIN inovacoes_ano n ON n.ano = coalesce(o.ano, i.ano)
FULL OUTER JOIN projetos_ano p ON p.ano = coalesce(o.ano, i.ano, n.ano)
ORDER BY 1;
COMMENT ON VIEW mart.vw_bi_visao_executiva IS 'Area 1 (visao executiva): principais indicadores do observatorio, por ano.';

-- 2) Indicadores por municipio.
CREATE OR REPLACE VIEW mart.vw_bi_indicadores_municipio AS
SELECT
    m.id_municipio,
    m.nome AS municipio,
    m.uf,
    m.pertence_area_atuacao,
    count(DISTINCT o.id_organizacao) AS qtd_organizacoes,
    count(DISTINCT o.id_organizacao) FILTER (WHERE o.ativa) AS qtd_organizacoes_ativas,
    coalesce(sum(fi.valor), 0) AS investimento_total,
    count(DISTINCT inov.id_inovacao) FILTER (WHERE inov.status = 'implementada') AS inovacoes_implementadas
FROM core.dim_municipio m
LEFT JOIN core.dim_organizacao o ON o.id_municipio = m.id_municipio
LEFT JOIN core.fato_investimento_inovacao fi ON fi.id_organizacao = o.id_organizacao
LEFT JOIN core.fato_inovacao inov ON inov.id_organizacao = o.id_organizacao
GROUP BY m.id_municipio, m.nome, m.uf, m.pertence_area_atuacao;
COMMENT ON VIEW mart.vw_bi_indicadores_municipio IS 'Area 2 (indicadores por municipio): organizacoes, investimento e inovacoes por municipio.';

-- 3) Indicadores por setor.
CREATE OR REPLACE VIEW mart.vw_bi_indicadores_setor AS
SELECT
    s.id_setor,
    s.nome AS setor,
    count(DISTINCT o.id_organizacao) AS qtd_organizacoes,
    coalesce(sum(fi.valor), 0) AS investimento_total,
    count(DISTINCT inov.id_inovacao) FILTER (WHERE inov.status = 'implementada') AS inovacoes_implementadas
FROM core.dim_setor s
LEFT JOIN core.dim_organizacao o ON o.id_setor = s.id_setor
LEFT JOIN core.fato_investimento_inovacao fi ON fi.id_organizacao = o.id_organizacao
LEFT JOIN core.fato_inovacao inov ON inov.id_organizacao = o.id_organizacao
GROUP BY s.id_setor, s.nome;
COMMENT ON VIEW mart.vw_bi_indicadores_setor IS 'Area 3 (indicadores por setor): organizacoes, investimento e inovacoes por setor economico.';

-- 4) Adocao tecnologica -> reaproveita o KPI ja definido.
CREATE OR REPLACE VIEW mart.vw_bi_adocao_tecnologica AS
SELECT * FROM mart.vw_adocao_tecnologia;
COMMENT ON VIEW mart.vw_bi_adocao_tecnologica IS 'Area 4 (adocao tecnologica): alias de mart.vw_adocao_tecnologia.';

-- 5) P&D e financiamento.
CREATE OR REPLACE VIEW mart.vw_bi_pd_financiamento AS
SELECT
    dt.ano,
    f.id_organizacao,
    f.investimento_p_d,
    f.faturamento,
    round(100.0 * f.investimento_p_d / NULLIF(f.faturamento, 0), 2) AS intensidade_p_d_pct
FROM core.fato_desempenho_organizacao f
JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo;
COMMENT ON VIEW mart.vw_bi_pd_financiamento IS 'Area 5 (P&D e financiamento): intensidade de P&D por organizacao/ano. Combine com mart.vw_investimento_por_fonte para o detalhamento por fonte de recurso.';

-- 6) Rede do ecossistema -> alias das views de rede.
CREATE OR REPLACE VIEW mart.vw_bi_rede_ecossistema AS
SELECT * FROM mart.vw_rede_conexoes_por_tipo;
COMMENT ON VIEW mart.vw_bi_rede_ecossistema IS 'Area 6 (rede do ecossistema): alias de mart.vw_rede_conexoes_por_tipo. Ver tambem mart.vw_rede_grau_organizacao e mart.vw_rede_densidade.';

-- 7) Inovacao e grau de novidade -> alias do KPI.
CREATE OR REPLACE VIEW mart.vw_bi_inovacao_grau_novidade AS
SELECT * FROM mart.vw_inovacao_por_grau_novidade;
COMMENT ON VIEW mart.vw_bi_inovacao_grau_novidade IS 'Area 7 (inovacao e grau de novidade): alias de mart.vw_inovacao_por_grau_novidade.';

-- 8) Impacto economico.
CREATE OR REPLACE VIEW mart.vw_bi_impacto_economico AS
SELECT
    coalesce(d.ano, i.ano) AS ano,
    d.faturamento_total,
    d.exportacoes_total,
    d.custos_reduzidos_total,
    i.receita_associada_total,
    i.reducao_custo_estimada_total,
    i.empregos_criados_total,
    i.empregos_qualificados_criados_total
FROM (
    SELECT dt.ano,
           sum(faturamento) AS faturamento_total,
           sum(exportacoes) AS exportacoes_total,
           sum(custos_reduzidos_por_inovacao) AS custos_reduzidos_total
    FROM core.fato_desempenho_organizacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
    GROUP BY dt.ano
) d
FULL OUTER JOIN (
    SELECT extract(year FROM data_implementacao)::smallint AS ano,
           sum(receita_associada) AS receita_associada_total,
           sum(reducao_custo_estimada) AS reducao_custo_estimada_total,
           sum(empregos_criados) AS empregos_criados_total,
           sum(empregos_qualificados_criados) AS empregos_qualificados_criados_total
    FROM core.fato_inovacao
    WHERE status = 'implementada' AND data_implementacao IS NOT NULL
    GROUP BY 1
) i ON i.ano = d.ano
ORDER BY 1;
COMMENT ON VIEW mart.vw_bi_impacto_economico IS 'Area 8 (impacto economico): faturamento, exportacoes, reducao de custo e empregos gerados por ano.';

-- 9) Empreendedorismo e destruicao criativa.
CREATE OR REPLACE VIEW mart.vw_bi_empreendedorismo AS
WITH entrada_ecossistema AS (
    SELECT extract(year FROM data_entrada_ecossistema)::smallint AS ano,
           count(*) AS novas_organizacoes,
           count(*) FILTER (WHERE tipo_organizacao = 'startup') AS novas_startups
    FROM core.dim_organizacao
    WHERE data_entrada_ecossistema IS NOT NULL
    GROUP BY 1
),
saidas AS (
    SELECT extract(year FROM o.atualizado_em)::smallint AS ano,
           count(DISTINCT o.id_organizacao) AS organizacoes_inativadas
    FROM core.dim_organizacao o
    WHERE NOT o.ativa
    GROUP BY 1
)
SELECT
    coalesce(e.ano, s.ano) AS ano,
    e.novas_organizacoes,
    e.novas_startups,
    s.organizacoes_inativadas
FROM entrada_ecossistema e
FULL OUTER JOIN saidas s ON s.ano = e.ano
ORDER BY 1;
COMMENT ON VIEW mart.vw_bi_empreendedorismo IS 'Area 9 (empreendedorismo e destruicao criativa): entrada de novas organizacoes/startups e saida (inativacao) por ano. organizacoes_inativadas e aproximado pela data da ultima atualizacao do registro.';

-- 10) Pipeline de inovacao (funil por status).
CREATE OR REPLACE VIEW mart.vw_bi_pipeline_inovacao AS
SELECT
    status,
    count(*) AS qtd_inovacoes,
    round(100.0 * count(*) / NULLIF(sum(count(*)) OVER (), 0), 2) AS pct_inovacoes
FROM core.fato_inovacao
GROUP BY status;
COMMENT ON VIEW mart.vw_bi_pipeline_inovacao IS 'Area 10 (pipeline de inovacao): funil de inovacoes por status (ideacao -> em_desenvolvimento -> piloto -> implementada/descontinuada).';
