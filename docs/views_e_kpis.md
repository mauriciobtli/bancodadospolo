# Views e KPIs do schema `mart`

Todas as views ficam em `mart` e podem ser consultadas diretamente pelo
Power BI com a role `powerbi_readonly`. Todas as divisoes usam `NULLIF` no
denominador — o resultado e `NULL` (não um erro) quando o denominador e
zero ou quando nao ha dados no periodo.

## KPIs obrigatorios (briefing, secao 7)

| View | Formula | Grao |
|---|---|---|
| `vw_taxa_empresas_inovadoras` | empresas com inovacao implementada no ano / **respondentes elegiveis** do ano * 100 | ano |
| `vw_intensidade_p_d` | investimento_p_d / faturamento * 100 | organizacao + ano |
| `vw_receita_proveniente_inovacao` | receita_produtos_novos / faturamento * 100 | organizacao + ano |
| `vw_produtividade_trabalhador` | faturamento / numero_empregados | organizacao + ano |
| `vw_taxa_primeira_inovacao` (renomeado de `vw_taxa_renovacao_empresarial_inovadora`) | empresas na 1a inovacao implementada no ano / respondentes elegiveis do ano * 100 | ano |
| `vw_conversao_projetos_inovacao` | projetos concluidos com inovacao implementada / projetos concluidos * 100 | global |
| `vw_conversao_conexoes_projetos` | conexoes que geraram projeto ou contrato / total de conexoes * 100 | global |
| `vw_investimento_por_inovacao` | investimento total / inovacoes implementadas | ano |
| `vw_adocao_tecnologia` | % de **respondentes elegiveis do ciclo** por tecnologia e nivel de adocao mais recente | ciclo + tecnologia + nivel |
| `vw_investimento_por_tecnologia` | valor e % de investimento por tecnologia principal do projeto financiado | tecnologia |
| `vw_investimento_por_setor` | valor e % de investimento por setor da organizacao investidora | setor |
| `vw_inovacao_por_grau_novidade` | quantidade e % de inovacoes por grau de novidade | grau de novidade |

Apoio: `vw_investimento_por_fonte` (valor/% de investimento por fonte de
recurso — usada tambem na area de P&D/financiamento do Power BI) e
`vw_conciliacao_investimento_pd` (ver secao "Fonte de verdade" abaixo).

### `vw_taxa_empresas_inovadoras` e `vw_adocao_tecnologia` usam respondentes elegiveis, nao "todas as ativas"

Essas duas views **não** dividem mais por "todas as organizacoes ativas"
nem usam `fato_desempenho_organizacao` como proxy de quem foi pesquisado.
O denominador agora vem de `mart.vw_respondentes_elegiveis`, construida a
partir de `core.universo_pesquisado` (quem estava no escopo de um ciclo de
coleta) `∩` `core.cobertura_coleta` (quem de fato respondeu). Isso separa
tres situacoes que antes eram indistinguiveis:

1. organizacao fora do universo pesquisado no ciclo — nao entra no
   denominador;
2. organizacao no universo mas que **nao respondeu** — nao entra no
   denominador (`cobertura_coleta.respondeu = false`, mas a linha existe,
   diferente de simplesmente nao ter dado nenhum);
3. organizacao que respondeu e **declarou explicitamente** nao usar uma
   tecnologia — entra no denominador (via `vw_respondentes_elegiveis`) e no
   numerador com `nivel_adocao = 0`.

**Pre-requisito operacional**: sem um `core.ciclo_coleta` cadastrado e
`universo_pesquisado`/`cobertura_coleta` preenchidos para o ano/ciclo, essas
views nao retornam nenhuma linha para aquele periodo (nao ha fallback
silencioso para "todas ativas"). Ver seção "Universo pesquisado e cobertura
de coleta" abaixo.

### Limitacao conhecida — `vw_investimento_por_tecnologia`

A tabela `fato_investimento_inovacao` nao tem tecnologia propria (o campo
nao existia no briefing original); a view so contabiliza investimentos que
tem `id_projeto` preenchido, herdando a tecnologia principal do projeto.
Investimentos sem projeto vinculado aparecem em `vw_investimento_por_fonte`
e `vw_investimento_por_setor`, mas nao em `vw_investimento_por_tecnologia`.

## Universo pesquisado e cobertura de coleta

| View | O que expõe |
|---|---|
| `dim_ciclo_coleta` | Rodadas de coleta/pesquisa (ex.: "Pesquisa Polo Inovale 2024") |
| `universo_pesquisado` | Sampling frame: quais organizacoes estavam no escopo de cada ciclo, e se elegiveis |
| `cobertura_coleta` | Quem efetivamente respondeu (ou nao) a cada ciclo |
| `vw_respondentes_elegiveis` | Organizacoes elegiveis que responderam — base do denominador dos KPIs de cobertura acima |

Para popular: cadastre um `ciclo_coleta` por rodada de pesquisa, insira
todas as organizacoes do escopo em `universo_pesquisado` (mesmo as que
depois nao respondem), e registre em `cobertura_coleta` se cada uma
respondeu. Toda carga de `fato_adocao_tecnologica` de uma rodada nova deve
preencher `id_ciclo` apontando para o ciclo correspondente.

## Fonte de verdade — investimento em P&D

Duas tabelas guardam numeros de P&D com propositos diferentes — **nunca
devem ser somadas entre si**:

| | `fato_desempenho_organizacao.investimento_p_d` | `fato_investimento_inovacao` (categoria=`p_d`) |
|---|---|---|
| Natureza | Total anual **autodeclarado** | Soma de lancamentos **categorizados** (por fonte de recurso/projeto) |
| Grao | Organizacao + ano (mesmo grao do `faturamento`) | Organizacao + periodo + fonte + categoria + projeto |
| Usado por | `vw_intensidade_p_d` (KPI oficial de intensidade de P&D) | `vw_investimento_por_fonte`, `vw_investimento_por_tecnologia`, `vw_investimento_por_setor`, `vw_investimento_por_inovacao` |
| Por que pode divergir | Autodeclarado, pode incluir gasto nao lancado em detalhe | So reflete o que foi lancado por categoria — pode estar incompleto |

Use `mart.vw_conciliacao_investimento_pd` para comparar as duas fontes por
organizacao/ano e investigar divergencias grandes — uma diferenca nao é
necessariamente um erro, mas vale checar se o lancamento categorizado
ficou incompleto.

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
| 9 | Empreendedorismo | `vw_bi_empreendedorismo` + `vw_cohort_sobrevivencia_empresarial` |
| 10 | Pipeline de inovacao | `vw_bi_pipeline_inovacao` |

`vw_cohort_sobrevivencia_empresarial` é um **snapshot** (não uma série
temporal completa) de sobrevivência por coorte de entrada no ecossistema —
estrutura preparada para evoluir, não a métrica final de renovação
empresarial pedida no briefing original (essa métrica completa exige
snapshots periódicos de status, que ainda não existem).

### Modelo para o Power BI

- Use apenas as views `mart.dim_*` e `mart.fato_*`/`mart.vw_*` como fonte —
  nunca conecte o Power BI a `raw`, `core` ou `etl`.
- `mart.fato_inovacao` ja vem achatado (tecnologia principal em coluna +
  lista textual de tecnologias relacionadas) para evitar relacionamento
  N:N no modelo. Se precisar do relacionamento N:N completo, use
  `mart.bridge_inovacao_tecnologia`, mas isso cria fanout — evite marcar
  como relacionamento ativo por padrao no Power BI.
- O mesmo vale para `mart.bridge_projeto_organizacao` (participantes do
  projeto com papel) e `mart.bridge_projeto_tecnologia` (tecnologias do
  projeto): use para analises especificas de multi-participante/
  multi-tecnologia, mas prefira `mart.dim_projeto.organizacao_lider_nome`
  e `tecnologia_principal_nome` para o caso comum, evitando fanout.
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
