-- =========================================================================
-- mart: KPIs obrigatorios (secao 7 do briefing)
-- Todas as divisoes usam NULLIF no denominador para evitar erro de divisao
-- por zero (retornam NULL em vez de falhar).
-- =========================================================================

-- 1. Empresas com >=1 inovacao implementada no ano / empresas acompanhadas no ano.
-- "Empresas acompanhadas" = organizacoes com registro de desempenho no ano
-- (proxy para "respondentes"; ajustar se houver fonte melhor de respondentes).
CREATE OR REPLACE VIEW mart.vw_taxa_empresas_inovadoras AS
WITH acompanhadas AS (
    SELECT dt.ano, count(DISTINCT f.id_organizacao) AS empresas_acompanhadas
    FROM core.fato_desempenho_organizacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
    GROUP BY dt.ano
),
inovadoras AS (
    SELECT extract(year FROM data_implementacao)::smallint AS ano,
           count(DISTINCT id_organizacao) AS empresas_inovadoras
    FROM core.fato_inovacao
    WHERE status = 'implementada' AND data_implementacao IS NOT NULL
    GROUP BY 1
)
SELECT
    a.ano,
    coalesce(i.empresas_inovadoras, 0) AS empresas_inovadoras,
    a.empresas_acompanhadas,
    round(100.0 * coalesce(i.empresas_inovadoras, 0) / NULLIF(a.empresas_acompanhadas, 0), 2) AS taxa_empresas_inovadoras_pct
FROM acompanhadas a
LEFT JOIN inovadoras i ON i.ano = a.ano;
COMMENT ON VIEW mart.vw_taxa_empresas_inovadoras IS 'Percentual de empresas acompanhadas com pelo menos uma inovacao implementada no ano.';

-- 2. Investimento em P&D / faturamento, por organizacao e ano.
CREATE OR REPLACE VIEW mart.vw_intensidade_p_d AS
SELECT
    f.id_organizacao,
    dt.ano,
    f.investimento_p_d,
    f.faturamento,
    round(100.0 * f.investimento_p_d / NULLIF(f.faturamento, 0), 2) AS intensidade_p_d_pct
FROM core.fato_desempenho_organizacao f
JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo;
COMMENT ON VIEW mart.vw_intensidade_p_d IS 'Intensidade de P&D: investimento_p_d / faturamento * 100, por organizacao e ano.';

-- 3. Receita de produtos/servicos novos / faturamento total.
CREATE OR REPLACE VIEW mart.vw_receita_proveniente_inovacao AS
SELECT
    f.id_organizacao,
    dt.ano,
    f.receita_produtos_novos,
    f.faturamento,
    round(100.0 * f.receita_produtos_novos / NULLIF(f.faturamento, 0), 2) AS receita_proveniente_inovacao_pct
FROM core.fato_desempenho_organizacao f
JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo;
COMMENT ON VIEW mart.vw_receita_proveniente_inovacao IS 'Percentual do faturamento proveniente de produtos/servicos novos.';

-- 4. Faturamento / numero de empregados.
CREATE OR REPLACE VIEW mart.vw_produtividade_trabalhador AS
SELECT
    f.id_organizacao,
    dt.ano,
    f.faturamento,
    f.numero_empregados,
    round(f.faturamento / NULLIF(f.numero_empregados, 0), 2) AS produtividade_por_trabalhador
FROM core.fato_desempenho_organizacao f
JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo;
COMMENT ON VIEW mart.vw_produtividade_trabalhador IS 'Faturamento por trabalhador (proxy de produtividade), por organizacao e ano.';

-- 5. Novas empresas inovadoras no periodo / total de empresas acompanhadas.
-- "Nova empresa inovadora" = organizacao cuja primeira inovacao implementada
-- ocorreu naquele ano.
CREATE OR REPLACE VIEW mart.vw_taxa_renovacao_empresarial_inovadora AS
WITH primeira_inovacao AS (
    SELECT id_organizacao, min(extract(year FROM data_implementacao))::smallint AS ano_primeira_inovacao
    FROM core.fato_inovacao
    WHERE status = 'implementada' AND data_implementacao IS NOT NULL
    GROUP BY id_organizacao
),
novas_por_ano AS (
    SELECT ano_primeira_inovacao AS ano, count(*) AS novas_empresas_inovadoras
    FROM primeira_inovacao
    GROUP BY 1
),
acompanhadas AS (
    SELECT dt.ano, count(DISTINCT f.id_organizacao) AS total_empresas_acompanhadas
    FROM core.fato_desempenho_organizacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
    GROUP BY dt.ano
)
SELECT
    a.ano,
    coalesce(n.novas_empresas_inovadoras, 0) AS novas_empresas_inovadoras,
    a.total_empresas_acompanhadas,
    round(100.0 * coalesce(n.novas_empresas_inovadoras, 0) / NULLIF(a.total_empresas_acompanhadas, 0), 2) AS taxa_renovacao_pct
FROM acompanhadas a
LEFT JOIN novas_por_ano n ON n.ano = a.ano;
COMMENT ON VIEW mart.vw_taxa_renovacao_empresarial_inovadora IS 'Percentual de empresas que estrearam como inovadoras no ano, sobre o total acompanhado.';

-- 6. Projetos concluidos que resultaram em inovacao implementada / projetos concluidos.
CREATE OR REPLACE VIEW mart.vw_conversao_projetos_inovacao AS
WITH concluidos AS (
    SELECT id_projeto FROM core.projeto WHERE status = 'concluido'
),
concluidos_com_inovacao AS (
    SELECT DISTINCT c.id_projeto
    FROM concluidos c
    JOIN core.fato_inovacao fi ON fi.id_projeto = c.id_projeto AND fi.status = 'implementada'
)
SELECT
    (SELECT count(*) FROM concluidos) AS projetos_concluidos,
    (SELECT count(*) FROM concluidos_com_inovacao) AS projetos_concluidos_com_inovacao,
    round(
        100.0 * (SELECT count(*) FROM concluidos_com_inovacao)
        / NULLIF((SELECT count(*) FROM concluidos), 0), 2
    ) AS taxa_conversao_pct;
COMMENT ON VIEW mart.vw_conversao_projetos_inovacao IS 'Percentual de projetos concluidos que geraram ao menos uma inovacao implementada.';

-- 7. Conexoes que geraram projeto ou contrato / total de conexoes.
CREATE OR REPLACE VIEW mart.vw_conversao_conexoes_projetos AS
SELECT
    count(*) AS total_conexoes,
    count(*) FILTER (WHERE gerou_projeto OR gerou_contrato) AS conexoes_com_resultado,
    round(
        100.0 * count(*) FILTER (WHERE gerou_projeto OR gerou_contrato)
        / NULLIF(count(*), 0), 2
    ) AS taxa_conversao_pct
FROM core.fato_conexao_ecossistema;
COMMENT ON VIEW mart.vw_conversao_conexoes_projetos IS 'Percentual de conexoes do ecossistema que geraram projeto ou contrato.';

-- 8. Investimento total em inovacao / numero de inovacoes implementadas, por ano.
CREATE OR REPLACE VIEW mart.vw_investimento_por_inovacao AS
WITH investimento_ano AS (
    SELECT dt.ano, sum(f.valor) AS total_investimento
    FROM core.fato_investimento_inovacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
    GROUP BY dt.ano
),
inovacoes_ano AS (
    SELECT extract(year FROM data_implementacao)::smallint AS ano, count(*) AS total_implementadas
    FROM core.fato_inovacao
    WHERE status = 'implementada' AND data_implementacao IS NOT NULL
    GROUP BY 1
)
SELECT
    coalesce(i.ano, n.ano) AS ano,
    i.total_investimento,
    n.total_implementadas,
    round(i.total_investimento / NULLIF(n.total_implementadas, 0), 2) AS investimento_medio_por_inovacao
FROM investimento_ano i
FULL OUTER JOIN inovacoes_ano n ON n.ano = i.ano;
COMMENT ON VIEW mart.vw_investimento_por_inovacao IS 'Investimento total em inovacao dividido pelo numero de inovacoes implementadas, por ano.';

-- 9. Percentual de organizacoes por tecnologia e nivel de adocao (estado mais recente por org+tecnologia).
CREATE OR REPLACE VIEW mart.vw_adocao_tecnologia AS
WITH estado_atual AS (
    SELECT DISTINCT ON (id_organizacao, id_tecnologia)
        id_organizacao, id_tecnologia, nivel_adocao
    FROM core.fato_adocao_tecnologica
    ORDER BY id_organizacao, id_tecnologia, id_tempo DESC
)
SELECT
    t.id_tecnologia,
    t.nome AS tecnologia,
    e.nivel_adocao,
    count(*) AS qtd_organizacoes,
    round(
        100.0 * count(*) / NULLIF((SELECT count(*) FROM core.dim_organizacao WHERE ativa), 0), 2
    ) AS pct_organizacoes_ativas
FROM estado_atual e
JOIN core.dim_tecnologia t ON t.id_tecnologia = e.id_tecnologia
GROUP BY t.id_tecnologia, t.nome, e.nivel_adocao;
COMMENT ON VIEW mart.vw_adocao_tecnologia IS 'Percentual de organizacoes ativas por tecnologia e nivel de adocao mais recente (0=nao utiliza .. 4=critica).';

-- Apoio: investimento por fonte de recurso (usado tambem na area de P&D/financiamento).
CREATE OR REPLACE VIEW mart.vw_investimento_por_fonte AS
SELECT
    fr.id_fonte_recurso,
    fr.nome AS fonte_recurso,
    sum(f.valor) AS valor_total,
    round(100.0 * sum(f.valor) / NULLIF(sum(sum(f.valor)) OVER (), 0), 2) AS pct_investimento
FROM core.fato_investimento_inovacao f
JOIN core.dim_fonte_recurso fr ON fr.id_fonte_recurso = f.id_fonte_recurso
GROUP BY fr.id_fonte_recurso, fr.nome;
COMMENT ON VIEW mart.vw_investimento_por_fonte IS 'Valor e percentual de investimento por fonte de recurso (proprio, FAPESC, FINEP, etc.).';

-- 10. Valor e percentual de investimento por tecnologia.
-- Limitacao: so contabiliza investimentos vinculados a um projeto
-- (fato_investimento_inovacao.id_projeto), pois a tecnologia e atributo do
-- projeto, nao do investimento em si. Investimentos sem projeto vinculado
-- nao aparecem aqui (ver mart.vw_investimento_por_fonte/setor para o total).
CREATE OR REPLACE VIEW mart.vw_investimento_por_tecnologia AS
SELECT
    t.id_tecnologia,
    t.nome AS tecnologia,
    sum(f.valor) AS valor_total,
    round(100.0 * sum(f.valor) / NULLIF(sum(sum(f.valor)) OVER (), 0), 2) AS pct_investimento
FROM core.fato_investimento_inovacao f
JOIN core.projeto p ON p.id_projeto = f.id_projeto
JOIN core.dim_tecnologia t ON t.id_tecnologia = p.id_tecnologia_principal
GROUP BY t.id_tecnologia, t.nome;
COMMENT ON VIEW mart.vw_investimento_por_tecnologia IS 'Valor e percentual de investimento por tecnologia principal do projeto financiado (requer id_projeto preenchido no investimento).';

-- 11. Valor e percentual de investimento por setor (setor da organizacao investidora).
CREATE OR REPLACE VIEW mart.vw_investimento_por_setor AS
SELECT
    s.id_setor,
    s.nome AS setor,
    sum(f.valor) AS valor_total,
    round(100.0 * sum(f.valor) / NULLIF(sum(sum(f.valor)) OVER (), 0), 2) AS pct_investimento
FROM core.fato_investimento_inovacao f
JOIN core.dim_organizacao o ON o.id_organizacao = f.id_organizacao
JOIN core.dim_setor s ON s.id_setor = o.id_setor
GROUP BY s.id_setor, s.nome;
COMMENT ON VIEW mart.vw_investimento_por_setor IS 'Valor e percentual de investimento por setor economico da organizacao investidora.';

-- 12. Quantidade e percentual de inovacoes por grau de novidade.
CREATE OR REPLACE VIEW mart.vw_inovacao_por_grau_novidade AS
SELECT
    g.id_grau_novidade,
    g.nome AS grau_novidade,
    g.ordem,
    count(fi.id_inovacao) AS qtd_inovacoes,
    round(100.0 * count(fi.id_inovacao) / NULLIF(sum(count(fi.id_inovacao)) OVER (), 0), 2) AS pct_inovacoes
FROM core.dim_grau_novidade g
LEFT JOIN core.fato_inovacao fi ON fi.id_grau_novidade = g.id_grau_novidade
GROUP BY g.id_grau_novidade, g.nome, g.ordem;
COMMENT ON VIEW mart.vw_inovacao_por_grau_novidade IS 'Quantidade e percentual de inovacoes por grau de novidade (empresa, regional, nacional, mundial).';
