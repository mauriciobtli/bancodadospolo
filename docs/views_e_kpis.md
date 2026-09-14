# Views e KPIs do schema `mart`

Todas as views ficam em `mart` e podem ser consultadas diretamente pelo
Power BI com a role `powerbi_readonly`. Todas as divisoes usam `NULLIF` no
denominador — o resultado e `NULL` (não um erro) quando o denominador e
zero ou quando nao ha dados no periodo.

## KPIs obrigatorios (briefing, secao 7)

| View | Formula | Grao |
|---|---|---|
| `vw_taxa_empresas_inovadoras` | empresas com inovacao implementada no ano / empresas acompanhadas no ano * 100 | ano |
| `vw_intensidade_p_d` | investimento_p_d / faturamento * 100 | organizacao + ano |
| `vw_receita_proveniente_inovacao` | receita_produtos_novos / faturamento * 100 | organizacao + ano |
| `vw_produtividade_trabalhador` | faturamento / numero_empregados | organizacao + ano |
| `vw_taxa_renovacao_empresarial_inovadora` | novas empresas inovadoras no ano / total acompanhado * 100 | ano |
| `vw_conversao_projetos_inovacao` | projetos concluidos com inovacao implementada / projetos concluidos * 100 | global |
| `vw_conversao_conexoes_projetos` | conexoes que geraram projeto ou contrato / total de conexoes * 100 | global |
| `vw_investimento_por_inovacao` | investimento total / inovacoes implementadas | ano |
| `vw_adocao_tecnologia` | % de organizacoes ativas por tecnologia e nivel de adocao mais recente | tecnologia + nivel |
| `vw_investimento_por_tecnologia` | valor e % de investimento por tecnologia principal do projeto financiado | tecnologia |
| `vw_investimento_por_setor` | valor e % de investimento por setor da organizacao investidora | setor |
| `vw_inovacao_por_grau_novidade` | quantidade e % de inovacoes por grau de novidade | grau de novidade |

Apoio: `vw_investimento_por_fonte` (valor/% de investimento por fonte de
recurso — usada tambem na area de P&D/financiamento do Power BI).

### Limitacao conhecida — `vw_investimento_por_tecnologia`

A tabela `fato_investimento_inovacao` nao tem tecnologia propria (o campo
nao existia no briefing original); a view so contabiliza investimentos que
tem `id_projeto` preenchido, herdando a tecnologia principal do projeto.
Investimentos sem projeto vinculado aparecem em `vw_investimento_por_fonte`
e `vw_investimento_por_setor`, mas nao em `vw_investimento_por_tecnologia`.

## Analise de rede (briefing, secao 8)

| View | O que calcula |
|---|---|
| `vw_rede_grau_organizacao` | Grau (numero de conexoes) de cada organizacao e ranking de conectividade |
| `vw_rede_densidade` | Densidade da rede = conexoes existentes / conexoes possiveis (grafo dirigido, so organizacoes ativas) |
| `vw_rede_conexoes_por_tipo` | Conexoes agregadas por par de tipo de organizacao e tipo de conexao — filtre `tipo_origem`/`tipo_destino` no Power BI para ver empresa-universidade, empresa-ICT, empresa-startup etc. |
| `vw_rede_conversao` | % de conexoes que geraram projeto, contrato ou inovacao |

Nenhum algoritmo avancado de grafo (centralidade, comunidades) foi
implementado nesta versao — as views entregam os agregados necessarios
para alimentar uma ferramenta de grafo (Python/NetworkX, Gephi) depois,
sem exigir mudanca de modelo.

## Views por area do Power BI (briefing, secao 11)

| # | Area | View |
|---|---|---|
| 1 | Visao executiva | `vw_bi_visao_executiva` |
| 2 | Indicadores por municipio | `vw_bi_indicadores_municipio` |
| 3 | Indicadores por setor | `vw_bi_indicadores_setor` |
| 4 | Adocao tecnologica | `vw_bi_adocao_tecnologica` (alias de `vw_adocao_tecnologia`) |
| 5 | P&D e financiamento | `vw_bi_pd_financiamento` + `vw_investimento_por_fonte` |
| 6 | Rede do ecossistema | `vw_bi_rede_ecossistema` (alias de `vw_rede_conexoes_por_tipo`) + `vw_rede_grau_organizacao` + `vw_rede_densidade` |
| 7 | Inovacao e grau de novidade | `vw_bi_inovacao_grau_novidade` (alias de `vw_inovacao_por_grau_novidade`) |
| 8 | Impacto economico | `vw_bi_impacto_economico` |
| 9 | Empreendedorismo | `vw_bi_empreendedorismo` |
| 10 | Pipeline de inovacao | `vw_bi_pipeline_inovacao` |

### Modelo para o Power BI

- Use apenas as views `mart.dim_*` e `mart.fato_*`/`mart.vw_*` como fonte —
  nunca conecte o Power BI a `raw`, `core` ou `etl`.
- `mart.fato_inovacao` ja vem achatado (tecnologia principal em coluna +
  lista textual de tecnologias relacionadas) para evitar relacionamento
  N:N no modelo. Se precisar do relacionamento N:N completo, use
  `mart.bridge_inovacao_tecnologia`, mas isso cria fanout — evite marcar
  como relacionamento ativo por padrao no Power BI.
- Monte as relacoes de estrela a partir de `mart.dim_tempo.id_tempo`,
  `mart.dim_organizacao.id_organizacao`, `mart.dim_municipio.id_municipio`,
  `mart.dim_setor.id_setor`, `mart.dim_tecnologia.id_tecnologia` etc.

## Exemplos de consulta

```sql
-- Intensidade de P&D das 10 organizacoes com maior investimento em 2024
SELECT o.nome, k.intensidade_p_d_pct
FROM mart.vw_intensidade_p_d k
JOIN mart.dim_organizacao o ON o.id_organizacao = k.id_organizacao
WHERE k.ano = 2024
ORDER BY k.intensidade_p_d_pct DESC NULLS LAST
LIMIT 10;

-- Organizacoes mais conectadas do ecossistema
SELECT nome, tipo_organizacao, grau
FROM mart.vw_rede_grau_organizacao
ORDER BY grau DESC
LIMIT 20;

-- Funil de inovacao (pipeline)
SELECT status, qtd_inovacoes, pct_inovacoes
FROM mart.vw_bi_pipeline_inovacao
ORDER BY qtd_inovacoes DESC;
```
