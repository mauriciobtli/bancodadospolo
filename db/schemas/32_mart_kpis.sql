-- =========================================================================
-- mart: KPIs obrigatorios (secao 7 do briefing)
-- Todas as divisoes usam NULLIF no denominador para evitar erro de divisao
-- por zero (retornam NULL em vez de falhar).
-- =========================================================================

-- 1. Empresas com >=1 inovacao implementada no ano / respondentes elegiveis do ano.
-- Denominador = mart.vw_respondentes_elegiveis (universo_pesquisado ∩
-- cobertura_coleta), nao mais "todas as organizacoes ativas" nem o antigo
-- proxy via fato_desempenho_organizacao. Numerador restrito aos proprios
-- respondentes elegiveis (uma organizacao fora do universo pesquisado nao
-- deve inflar a taxa mesmo que tenha inovado).
CREATE OR REPLACE VIEW mart.vw_taxa_empresas_inovadoras AS
WITH respondentes AS (
    SELECT ano, count(DISTINCT id_organizacao) AS empresas_respondentes
    FROM mart.vw_respondentes_elegiveis
    GROUP BY ano
),
inovadoras AS (
    SELECT re.ano, count(DISTINCT fi.id_organizacao) AS empresas_inovadoras
    FROM core.fato_inovacao fi
    JOIN mart.vw_respondentes_elegiveis re
        ON re.id_organizacao = fi.id_organizacao
        AND re.ano = extract(year FROM fi.data_implementacao)::smallint
    WHERE fi.status = 'implementada' AND fi.data_implementacao IS NOT NULL
    GROUP BY re.ano
)
SELECT
    r.ano,
    coalesce(i.empresas_inovadoras, 0) AS empresas_inovadoras,
    r.empresas_respondentes,
    round(100.0 * coalesce(i.empresas_inovadoras, 0) / NULLIF(r.empresas_respondentes, 0), 2) AS taxa_empresas_inovadoras_pct
FROM respondentes r
LEFT JOIN inovadoras i ON i.ano = r.ano;
COMMENT ON VIEW mart.vw_taxa_empresas_inovadoras IS 'Percentual de respondentes elegiveis (mart.vw_respondentes_elegiveis) com pelo menos uma inovacao implementada no ano. Requer ciclo_coleta/universo_pesquisado/cobertura_coleta preenchidos para o ano — sem isso, o ano nao aparece (nao ha "todas ativas" como fallback).';

-- 2. Investimento em P&D / faturamento, por organizacao e ano.
-- Fonte de verdade: ver COMMENT ON COLUMN core.fato_desempenho_organizacao.investimento_p_d.
CREATE OR REPLACE VIEW mart.vw_intensidade_p_d AS
SELECT
    f.id_organizacao,
    dt.ano,
    f.investimento_p_d,
    f.faturamento,
    round(100.0 * f.investimento_p_d / NULLIF(f.faturamento, 0), 2) AS intensidade_p_d_pct
FROM core.fato_desempenho_organizacao f
JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo;
COMMENT ON VIEW mart.vw_intensidade_p_d IS 'Intensidade de P&D: investimento_p_d / faturamento * 100, por organizacao e ano. Fonte de verdade para este KPI e core.fato_desempenho_organizacao.investimento_p_d (autodeclarado, mesmo grao do faturamento) — ver mart.vw_conciliacao_investimento_pd para comparar com o detalhamento categorizado.';

-- Apoio: concilia as duas fontes de investimento em P&D (nunca somar uma na outra).
CREATE OR REPLACE VIEW mart.vw_conciliacao_investimento_pd AS
WITH autodeclarado AS (
    SELECT f.id_organizacao, dt.ano, f.investimento_p_d AS investimento_p_d_autodeclarado
    FROM core.fato_desempenho_organizacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
),
categorizado AS (
    SELECT f.id_organizacao, dt.ano, sum(f.valor) AS investimento_p_d_categorizado
    FROM core.fato_investimento_inovacao f
    JOIN core.dim_tempo dt ON dt.id_tempo = f.id_tempo
    WHERE f.categoria = 'p_d'
    GROUP BY f.id_organizacao, dt.ano
)
SELECT
    coalesce(a.id_organizacao, c.id_organizacao) AS id_organizacao,
    coalesce(a.ano, c.ano) AS ano,
    a.investimento_p_d_autodeclarado,
    c.investimento_p_d_categorizado,
    a.investimento_p_d_autodeclarado - coalesce(c.investimento_p_d_categorizado, 0) AS diferenca,
    round(
        100.0 * abs(a.investimento_p_d_autodeclarado - coalesce(c.investimento_p_d_categorizado, 0))
        / NULLIF(a.investimento_p_d_autodeclarado, 0), 2
    ) AS diferenca_pct
FROM autodeclarado a
FULL OUTER JOIN categorizado c ON c.id_organizacao = a.id_organizacao AND c.ano = a.ano;
COMMENT ON VIEW mart.vw_conciliacao_investimento_pd IS 'Compara, por organizacao e ano, o P&D autodeclarado (fato_desempenho_organizacao.investimento_p_d) com a soma categorizada (fato_investimento_inovacao, categoria=''p_d''). Divergencia grande pode indicar lancamento incompleto por categoria — nao e um erro de sistema, e uma diferenca esperada entre dois instrumentos de coleta distintos.';

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

-- 5. Empresas em sua PRIMEIRA inovacao implementada no ano / respondentes elegiveis do ano.
--
-- Renomeado de vw_taxa_renovacao_empresarial_inovadora: o nome antigo
-- sugeria medir renovacao empresarial (entrada de novas empresas/startups,
-- sobrevivencia), mas na verdade mede algo mais especifico — organizacoes
-- que inovaram pela primeira vez no periodo. Renovacao empresarial de
-- verdade (natalidade, mortalidade, sobrevivencia por coorte) tem
-- estrutura propria em mart.vw_cohort_sobrevivencia_empresarial e
-- mart.vw_bi_empreendedorismo, a partir de
-- core.dim_organizacao.data_entrada_ecossistema/data_saida_ecossistema.
DROP VIEW IF EXISTS mart.vw_taxa_renovacao_empresarial_inovadora;

CREATE OR REPLACE VIEW mart.vw_taxa_primeira_inovacao AS
WITH primeira_inovacao AS (
    SELECT id_organizacao, min(extract(year FROM data_implementacao))::smallint AS ano_primeira_inovacao
    FROM core.fato_inovacao
    WHERE status = 'implementada' AND data_implementacao IS NOT NULL
    GROUP BY id_organizacao
),
novas_por_ano AS (
    SELECT re.ano, count(*) AS empresas_primeira_inovacao
    FROM primeira_inovacao pi
    JOIN mart.vw_respondentes_elegiveis re
        ON re.id_organizacao = pi.id_organizacao AND re.ano = pi.ano_primeira_inovacao
    GROUP BY re.ano
),
respondentes AS (
    SELECT ano, count(DISTINCT id_organizacao) AS empresas_respondentes
    FROM mart.vw_respondentes_elegiveis
    GROUP BY ano
)
SELECT
    r.ano,
    coalesce(n.empresas_primeira_inovacao, 0) AS empresas_primeira_inovacao,
    r.empresas_respondentes,
    round(100.0 * coalesce(n.empresas_primeira_inovacao, 0) / NULLIF(r.empresas_respondentes, 0), 2) AS taxa_primeira_inovacao_pct
FROM respondentes r
LEFT JOIN novas_por_ano n ON n.ano = r.ano;
COMMENT ON VIEW mart.vw_taxa_primeira_inovacao IS 'Percentual de respondentes elegiveis do ano que implementaram sua PRIMEIRA inovacao naquele ano. Nao e uma medida de renovacao empresarial (entrada/saida de organizacoes) — para isso, ver mart.vw_cohort_sobrevivencia_empresarial.';

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

-- 9. Percentual de organizacoes por tecnologia e nivel de adocao, por ciclo de coleta.
--
-- Denominador = respondentes elegiveis do MESMO ciclo (mart.vw_respondentes_elegiveis),
-- nao mais "todas as organizacoes ativas". Isso distingue corretamente:
--   - organizacao fora do universo pesquisado ou nao-respondente: nao entra
--     no denominador nem no numerador (nao aparece nesta view);
--   - organizacao respondente que DECLAROU nao utilizar uma tecnologia:
--     aparece no numerador com nivel_adocao=0 (e conta no denominador via
--     vw_respondentes_elegiveis, mesmo sem nenhuma linha "positiva").
-- Requer core.fato_adocao_tecnologica.id_ciclo preenchido; registros sem
-- ciclo (dado legado anterior a esta estrutura) ficam de fora — use
-- mart.fato_adocao_tecnologica para consultar o historico bruto sem esse filtro.
CREATE OR REPLACE VIEW mart.vw_adocao_tecnologia AS
WITH estado_atual AS (
    SELECT DISTINCT ON (id_organizacao, id_tecnologia)
        id_organizacao, id_tecnologia, id_ciclo, nivel_adocao
    FROM core.fato_adocao_tecnologica
    WHERE id_ciclo IS NOT NULL
    ORDER BY id_organizacao, id_tecnologia, id_tempo DESC
),
respondentes_por_ciclo AS (
    SELECT id_ciclo, count(DISTINCT id_organizacao) AS total_respondentes
    FROM mart.vw_respondentes_elegiveis
    GROUP BY id_ciclo
)
SELECT
    e.id_ciclo,
    ciclo.nome AS ciclo_coleta,
    ciclo.ano_referencia AS ano,
    t.id_tecnologia,
    t.nome AS tecnologia,
    e.nivel_adocao,
    count(*) AS qtd_organizacoes,
    rp.total_respondentes,
    round(100.0 * count(*) / NULLIF(rp.total_respondentes, 0), 2) AS pct_organizacoes_respondentes
FROM estado_atual e
JOIN core.dim_tecnologia t ON t.id_tecnologia = e.id_tecnologia
JOIN core.ciclo_coleta ciclo ON ciclo.id_ciclo = e.id_ciclo
LEFT JOIN respondentes_por_ciclo rp ON rp.id_ciclo = e.id_ciclo
GROUP BY e.id_ciclo, ciclo.nome, ciclo.ano_referencia, t.id_tecnologia, t.nome, e.nivel_adocao, rp.total_respondentes;
COMMENT ON VIEW mart.vw_adocao_tecnologia IS 'Percentual de respondentes elegiveis (por ciclo de coleta) em cada nivel de adocao de cada tecnologia (0=declarou nao utilizar .. 4=critica). Organizacao nao-respondente ou fora do universo pesquisado nao aparece aqui.';

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
