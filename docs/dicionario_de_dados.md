# Dicionario de dados

Gerado a partir do banco real (`information_schema` + comentarios SQL) apos `alembic upgrade head`, cobrindo os schemas `core` (dados limpos) e `mart` (consumido pelo Power BI). Para regenerar apos uma mudanca de schema, use a consulta SQL no rodape deste documento.


## Schema `core`


### `core.bridge_inovacao_tecnologia`


Ponte N:N entre inovacao e tecnologias habilitadoras. principal marca a tecnologia mais relevante da inovacao (usada para achatar em mart).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_inovacao` | bigint | nao |  |
| `id_tecnologia` | bigint | nao |  |
| `principal` | boolean | nao |  |
| `criado_em` | timestamp with time zone | nao |  |


### `core.bridge_projeto_organizacao`


Participantes de um projeto e seus papeis funcionais (N:N). Permite multiplos parceiros/executores/financiadores por projeto, e multiplos papeis para a mesma organizacao. O tipo da organizacao (universidade, ICT, empresa...) vem de dim_organizacao.tipo_organizacao, nao deste campo.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_projeto` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `papel` | text | nao |  |
| `data_entrada` | date | sim |  |
| `data_saida` | date | sim |  |
| `fonte_dado` | text | nao |  |
| `criado_em` | timestamp with time zone | nao |  |


### `core.bridge_projeto_tecnologia`


Tecnologias associadas a um projeto (N:N). principal marca a tecnologia mais relevante; mantida em sincronia com core.projeto.id_tecnologia_principal pelos triggers abaixo.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_projeto` | bigint | nao |  |
| `id_tecnologia` | bigint | nao |  |
| `principal` | boolean | nao |  |
| `criado_em` | timestamp with time zone | nao |  |


### `core.ciclo_coleta`


Uma rodada de coleta/pesquisa (ex.: "Pesquisa Polo Inovale 2024"). Base temporal para universo_pesquisado e cobertura_coleta.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | nao |  |
| `nome` | text | nao |  |
| `ano_referencia` | smallint | nao |  |
| `data_inicio` | date | sim |  |
| `data_fim` | date | sim |  |
| `tipo_cobertura` | text | nao |  |
| `descricao` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.cobertura_coleta`


Registra, por organizacao e ciclo, se houve resposta efetiva. So pode existir cobertura para um par (id_ciclo, id_organizacao) que ja esteja em universo_pesquisado (FK composta). Junto com universo_pesquisado, forma a base de "respondentes elegiveis" usada como denominador dos KPIs de cobertura (ver mart.vw_respondentes_elegiveis).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `respondeu` | boolean | nao |  |
| `data_resposta` | date | sim |  |
| `instrumento` | text | sim | Como a resposta foi coletada: formulario, entrevista, planilha, etc. |
| `observacao` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.contato_organizacao`


Dados pessoais de contato (LGPD). Nunca exposto em mart nem para a role powerbi_readonly.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_contato` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `nome_contato` | text | sim |  |
| `email` | text | sim |  |
| `telefone` | text | sim |  |
| `cargo` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_fonte_recurso`


Origem do recurso financeiro (proprio, fapesc, finep, investidor, etc.).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fonte_recurso` | bigint | nao |  |
| `codigo` | text | nao |  |
| `nome` | text | nao |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_grau_novidade`


Escala ordinal de novidade da inovacao (1=empresa .. 4=mundial). Coluna ordem permite comparacoes >=/<=.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_grau_novidade` | bigint | nao |  |
| `codigo` | text | nao |  |
| `nome` | text | nao |  |
| `ordem` | smallint | nao |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_municipio`


Municipios de referencia. pertence_area_atuacao marca os municipios cobertos pelo Polo Inovale.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_municipio` | bigint | nao |  |
| `codigo_ibge` | character varying | nao |  |
| `nome` | text | nao |  |
| `uf` | character | nao |  |
| `regiao` | text | nao |  |
| `pertence_area_atuacao` | boolean | nao |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_organizacao`


Empresas, startups, universidades, ICTs, governo, associacoes etc. Apenas dados publicos/institucionais.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_organizacao` | bigint | nao |  |
| `nome` | text | nao |  |
| `nome_fantasia` | text | sim |  |
| `cnpj` | character varying | sim | Somente digitos (14), validado por ck_organizacao_cnpj_formato e pelo validador de digito verificador no ETL. Nulo permitido para entidades sem CNPJ (coletivos, grupos de pesquisa). |
| `tipo_organizacao` | text | nao |  |
| `id_municipio` | bigint | sim |  |
| `id_setor` | bigint | sim |  |
| `porte` | text | nao |  |
| `ano_fundacao` | smallint | sim |  |
| `site` | text | sim |  |
| `ativa` | boolean | nao |  |
| `data_entrada_ecossistema` | date | sim |  |
| `data_saida_ecossistema` | date | sim | Complementa data_entrada_ecossistema: quando preenchida (junto com ativa=false), registra quando a organizacao deixou de fazer parte do ecossistema acompanhado. Base para futuras metricas de sobrevivencia/renovacao empresarial (ver mart.vw_cohort_sobrevivencia_empresarial). |
| `motivo_saida` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_problema_alvo`


Problema de negocio que a inovacao/projeto busca resolver (produtividade, custo, escassez de mao de obra, etc.).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_problema_alvo` | bigint | nao |  |
| `codigo` | text | nao |  |
| `nome` | text | nao |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_setor`


Setores economicos das organizacoes e projetos.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_setor` | bigint | nao |  |
| `codigo` | text | nao |  |
| `nome` | text | nao |  |
| `descricao` | text | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_tecnologia`


Catalogo de tecnologias habilitadoras (IA, IoT, biotecnologia, etc.).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_tecnologia` | bigint | nao |  |
| `codigo` | text | nao |  |
| `nome` | text | nao |  |
| `descricao` | text | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.dim_tempo`


Dimensao calendario, grao diario. id_tempo = AAAAMMDD, populada via seed (generate_series).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_tempo` | bigint | nao |  |
| `data` | date | nao |  |
| `dia` | smallint | nao |  |
| `mes` | smallint | nao |  |
| `nome_mes` | text | nao |  |
| `trimestre` | smallint | nao |  |
| `ano` | smallint | nao |  |
| `criado_em` | timestamp with time zone | nao |  |


### `core.dim_tipo_inovacao`


Categoria da inovacao: produto, servico, processo, modelo de negocio, tecnologia habilitadora.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_tipo_inovacao` | bigint | nao |  |
| `codigo` | text | nao |  |
| `nome` | text | nao |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.fato_adocao_tecnologica`


Nivel de adocao de cada tecnologia por organizacao e periodo. 0=nao utiliza .. 4=tecnologia critica.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `id_tecnologia` | bigint | nao |  |
| `id_tempo` | bigint | nao |  |
| `nivel_adocao` | smallint | nao |  |
| `ano_inicio_uso` | smallint | sim |  |
| `area_aplicacao` | text | sim |  |
| `observacao` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |
| `id_ciclo` | bigint | sim | Ciclo de coleta que originou esta medicao. Obrigatorio, na pratica, para que a organizacao entre no denominador de mart.vw_adocao_tecnologia (respondentes elegiveis do ciclo). |


### `core.fato_conexao_ecossistema`


Relacao dirigida entre dois atores do ecossistema (pesquisa, parceria, contrato, mentoria etc.), base para analise de rede.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_conexao` | bigint | nao |  |
| `id_organizacao_origem` | bigint | nao |  |
| `id_organizacao_destino` | bigint | nao |  |
| `tipo_conexao` | text | nao |  |
| `data_inicio` | date | sim |  |
| `data_fim` | date | sim |  |
| `id_projeto` | bigint | sim |  |
| `valor_financeiro` | numeric | sim |  |
| `gerou_projeto` | boolean | nao |  |
| `gerou_contrato` | boolean | nao |  |
| `gerou_inovacao` | boolean | nao |  |
| `id_origem_externa` | text | sim | Identificador estavel do registro na fonte, para permitir upsert idempotente em reprocessamentos (mesmo mecanismo de fato_inovacao.id_origem_externa). |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.fato_desempenho_organizacao`


Indicadores anuais de desempenho economico-financeiro por organizacao. Nunca atualiza um ano fechado com valor de outro ano.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `id_tempo` | bigint | nao |  |
| `faturamento` | numeric | sim |  |
| `numero_empregados` | integer | sim |  |
| `numero_empregados_tecnologia` | integer | sim |  |
| `exportacoes` | numeric | sim |  |
| `receita_produtos_novos` | numeric | sim |  |
| `investimento_p_d` | numeric | sim | FONTE DE VERDADE para o KPI "intensidade de P&D" (mart.vw_intensidade_p_d = investimento_p_d / faturamento), por ser autodeclarado no MESMO grao e pela MESMA fonte que o faturamento (evita comparar numerador e denominador de levantamentos diferentes). E um total anual autodeclarado, podendo divergir da soma categorizada em core.fato_investimento_inovacao (categoria='p_d'), que e mais granular (por fonte de recurso/projeto) mas pode estar incompleta se nem todo investimento foi lancado por categoria. As duas metricas NUNCA devem ser somadas entre si; para investigar divergencias, use mart.vw_conciliacao_investimento_pd. |
| `custos_reduzidos_por_inovacao` | numeric | sim |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.fato_inovacao`


Uma inovacao individual (produto, servico, processo, modelo de negocio ou tecnologia habilitadora) implementada por uma organizacao.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_inovacao` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `id_projeto` | bigint | sim |  |
| `nome` | text | nao |  |
| `descricao` | text | sim |  |
| `id_tipo_inovacao` | bigint | nao |  |
| `id_grau_novidade` | bigint | nao |  |
| `id_problema_alvo` | bigint | sim |  |
| `data_inicio` | date | sim |  |
| `data_implementacao` | date | sim |  |
| `status` | text | nao |  |
| `chegou_ao_mercado` | boolean | nao |  |
| `mercado_alvo` | text | sim |  |
| `impacto_trabalho` | text | sim |  |
| `receita_associada` | numeric | sim |  |
| `reducao_custo_estimada` | numeric | sim |  |
| `aumento_capacidade_percentual` | numeric | sim |  |
| `empregos_criados` | integer | nao |  |
| `empregos_qualificados_criados` | integer | nao |  |
| `id_origem_externa` | text | sim | Identificador estavel do registro na fonte (ex.: id de resposta de formulario, ou '<arquivo_origem>#<linha_origem>' quando a fonte nao tem id proprio). Junto com o indice unico parcial abaixo, permite ao ETL fazer INSERT ... ON CONFLICT (id_origem_externa) DO UPDATE em reprocessamentos, evitando duplicar a mesma inovacao a cada nova carga do mesmo arquivo. |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.fato_investimento_inovacao`


Investimentos em inovacao por organizacao, periodo, fonte de recurso e categoria.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `id_tempo` | bigint | nao |  |
| `id_fonte_recurso` | bigint | nao |  |
| `id_projeto` | bigint | sim | Vinculo opcional ao projeto financiado. Usado pelas views mart.vw_investimento_por_tecnologia/setor para herdar a tecnologia/setor do projeto quando o investimento nao e diretamente ligado a organizacao. |
| `categoria` | text | nao | FONTE DE VERDADE para o detalhamento de investimento em P&D por fonte de recurso/projeto/tecnologia (categoria = 'p_d'): soma de core.fato_investimento_inovacao.valor WHERE categoria='p_d'. E uma fonte DIFERENTE de core.fato_desempenho_organizacao.investimento_p_d (total anual autodeclarado pela organizacao) — nao devem ser somadas nem comparadas como se fossem a mesma medida. Ver comentario em fato_desempenho_organizacao.investimento_p_d e mart.vw_conciliacao_investimento_pd. |
| `valor` | numeric | nao |  |
| `observacao` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.fato_propriedade_intelectual`


Ativos de propriedade intelectual (patentes, marcas, software, cultivares) gerados pelas organizacoes.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_pi` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `id_projeto` | bigint | sim |  |
| `tipo_pi` | text | nao |  |
| `titulo` | text | nao |  |
| `numero_registro` | text | sim |  |
| `data_deposito` | date | sim |  |
| `data_concessao` | date | sim |  |
| `status` | text | nao |  |
| `licenciada` | boolean | nao |  |
| `receita_licenciamento` | numeric | sim |  |
| `id_origem_externa` | text | sim | Identificador estavel do registro na fonte (ex.: numero_registro quando existir, ou o mesmo padrao de fato_inovacao.id_origem_externa), para upsert idempotente em reprocessamentos. |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.fato_talento`


Capital humano e conhecimento por organizacao e periodo (pesquisadores, mestres, doutores, STEM).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `id_tempo` | bigint | nao |  |
| `pesquisadores_p_d` | integer | nao |  |
| `mestres` | integer | nao |  |
| `doutores` | integer | nao |  |
| `profissionais_stem` | integer | nao |  |
| `pessoas_capacitadas` | integer | nao |  |
| `novas_contratacoes_qualificadas` | integer | nao |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.projeto`


Projetos de inovacao/P&D. valor_total e orcado/planejado; investimento realizado vem de core.fato_investimento_inovacao.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_projeto` | bigint | nao |  |
| `nome` | text | nao |  |
| `descricao` | text | sim |  |
| `id_organizacao_lider` | bigint | sim | Fonte de verdade de quem lidera o projeto. Triggers em 23_core_bridges.sql mantem core.bridge_projeto_organizacao (papel='lider') sincronizada automaticamente com este campo, e bloqueiam edicao direta da bridge que divirja dele. |
| `data_inicio` | date | sim |  |
| `data_fim_prevista` | date | sim |  |
| `data_fim_real` | date | sim |  |
| `status` | text | nao |  |
| `valor_total` | numeric | sim |  |
| `id_fonte_principal` | bigint | sim |  |
| `id_setor` | bigint | sim |  |
| `id_tecnologia_principal` | bigint | sim | Fonte de verdade da tecnologia principal do projeto. Triggers em 23_core_bridges.sql mantem core.bridge_projeto_tecnologia.principal sincronizada automaticamente com este campo, e bloqueiam edicao direta da bridge que divirja dele. |
| `id_problema_alvo` | bigint | sim |  |
| `sustentabilidade` | boolean | sim | Classificacao de direcionalidade: o projeto tem foco em sustentabilidade (booleano simples nesta primeira versao). |
| `automacao` | boolean | sim | Classificacao de direcionalidade: o projeto envolve automacao (booleano simples nesta primeira versao). |
| `impacto_trabalho` | text | sim |  |
| `mercado_alvo` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `data_coleta` | date | sim |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


### `core.universo_pesquisado`


Sampling frame: organizacoes dentro do escopo de um ciclo de coleta. elegivel=false registra exclusoes (ex.: organizacao encerrada antes do ciclo) sem apagar a linha.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | nao |  |
| `id_organizacao` | bigint | nao |  |
| `elegivel` | boolean | nao |  |
| `motivo_inelegibilidade` | text | sim |  |
| `fonte_dado` | text | nao |  |
| `criado_em` | timestamp with time zone | nao |  |
| `atualizado_em` | timestamp with time zone | nao |  |


## Schema `mart`


### `mart.bridge_inovacao_tecnologia`


Relacionamento N:N explicito inovacao-tecnologia. Usar com cautela no Power BI (cria fanout); prefira mart.fato_inovacao para o caso geral.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_inovacao` | bigint | sim |  |
| `id_tecnologia` | bigint | sim |  |
| `principal` | boolean | sim |  |


### `mart.bridge_projeto_organizacao`


Participantes de cada projeto e seus papeis (lider, parceiro, executor, financiador, universidade, ICT, fornecedor...). N:N — use com cautela no Power BI (fanout); mart.dim_projeto.organizacao_lider_nome cobre o caso comum de "quem lidera".


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_projeto` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `organizacao_nome` | text | sim |  |
| `tipo_organizacao` | text | sim |  |
| `papel` | text | sim |  |
| `data_entrada` | date | sim |  |
| `data_saida` | date | sim |  |


### `mart.bridge_projeto_tecnologia`


Tecnologias associadas a cada projeto (N:N). Use com cautela no Power BI (fanout); mart.dim_projeto.tecnologia_principal_nome cobre o caso comum de "tecnologia principal".


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_projeto` | bigint | sim |  |
| `id_tecnologia` | bigint | sim |  |
| `tecnologia_nome` | text | sim |  |
| `principal` | boolean | sim |  |


### `mart.cobertura_coleta`


Quem efetivamente respondeu (ou nao) a cada ciclo de coleta.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `organizacao_nome` | text | sim |  |
| `respondeu` | boolean | sim |  |
| `data_resposta` | date | sim |  |
| `instrumento` | text | sim |  |


### `mart.dim_ciclo_coleta`


Rodadas de coleta/pesquisa (ex.: "Pesquisa Polo Inovale 2024").


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | sim |  |
| `nome` | text | sim |  |
| `ano_referencia` | smallint | sim |  |
| `data_inicio` | date | sim |  |
| `data_fim` | date | sim |  |
| `tipo_cobertura` | text | sim |  |
| `descricao` | text | sim |  |


### `mart.dim_fonte_recurso`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fonte_recurso` | bigint | sim |  |
| `codigo` | text | sim |  |
| `nome` | text | sim |  |


### `mart.dim_grau_novidade`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_grau_novidade` | bigint | sim |  |
| `codigo` | text | sim |  |
| `nome` | text | sim |  |
| `ordem` | smallint | sim |  |


### `mart.dim_municipio`


Municipios de referencia e area de atuacao do Polo Inovale.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_municipio` | bigint | sim |  |
| `codigo_ibge` | character varying | sim |  |
| `nome` | text | sim |  |
| `uf` | character | sim |  |
| `regiao` | text | sim |  |
| `pertence_area_atuacao` | boolean | sim |  |


### `mart.dim_organizacao`


Organizacoes do ecossistema, apenas dados publicos/institucionais (sem contato pessoal).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_organizacao` | bigint | sim |  |
| `nome` | text | sim |  |
| `nome_fantasia` | text | sim |  |
| `cnpj` | character varying | sim |  |
| `tipo_organizacao` | text | sim |  |
| `id_municipio` | bigint | sim |  |
| `municipio_nome` | text | sim |  |
| `uf` | character | sim |  |
| `id_setor` | bigint | sim |  |
| `setor_nome` | text | sim |  |
| `porte` | text | sim |  |
| `ano_fundacao` | smallint | sim |  |
| `site` | text | sim |  |
| `ativa` | boolean | sim |  |
| `data_entrada_ecossistema` | date | sim |  |
| `data_saida_ecossistema` | date | sim |  |
| `motivo_saida` | text | sim |  |


### `mart.dim_problema_alvo`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_problema_alvo` | bigint | sim |  |
| `codigo` | text | sim |  |
| `nome` | text | sim |  |


### `mart.dim_projeto`


Projetos com nomes de dimensoes relacionadas ja resolvidos, para simplificar o modelo consumido pelo Power BI.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_projeto` | bigint | sim |  |
| `nome` | text | sim |  |
| `descricao` | text | sim |  |
| `id_organizacao_lider` | bigint | sim |  |
| `organizacao_lider_nome` | text | sim |  |
| `data_inicio` | date | sim |  |
| `data_fim_prevista` | date | sim |  |
| `data_fim_real` | date | sim |  |
| `status` | text | sim |  |
| `valor_total` | numeric | sim |  |
| `id_fonte_principal` | bigint | sim |  |
| `fonte_principal_nome` | text | sim |  |
| `id_setor` | bigint | sim |  |
| `setor_nome` | text | sim |  |
| `id_tecnologia_principal` | bigint | sim |  |
| `tecnologia_principal_nome` | text | sim |  |
| `id_problema_alvo` | bigint | sim |  |
| `problema_alvo_nome` | text | sim |  |
| `sustentabilidade` | boolean | sim |  |
| `automacao` | boolean | sim |  |
| `impacto_trabalho` | text | sim |  |
| `mercado_alvo` | text | sim |  |


### `mart.dim_setor`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_setor` | bigint | sim |  |
| `codigo` | text | sim |  |
| `nome` | text | sim |  |
| `descricao` | text | sim |  |


### `mart.dim_tecnologia`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_tecnologia` | bigint | sim |  |
| `codigo` | text | sim |  |
| `nome` | text | sim |  |
| `descricao` | text | sim |  |


### `mart.dim_tempo`


Dimensao calendario (grao diario) para uso no Power BI.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_tempo` | bigint | sim |  |
| `data` | date | sim |  |
| `dia` | smallint | sim |  |
| `mes` | smallint | sim |  |
| `nome_mes` | text | sim |  |
| `trimestre` | smallint | sim |  |
| `ano` | smallint | sim |  |


### `mart.dim_tipo_inovacao`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_tipo_inovacao` | bigint | sim |  |
| `codigo` | text | sim |  |
| `nome` | text | sim |  |


### `mart.fato_adocao_tecnologica`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `id_tecnologia` | bigint | sim |  |
| `id_tempo` | bigint | sim |  |
| `nivel_adocao` | smallint | sim |  |
| `ano_inicio_uso` | smallint | sim |  |
| `area_aplicacao` | text | sim |  |
| `observacao` | text | sim |  |


### `mart.fato_conexao_ecossistema`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_conexao` | bigint | sim |  |
| `id_organizacao_origem` | bigint | sim |  |
| `organizacao_origem_nome` | text | sim |  |
| `tipo_organizacao_origem` | text | sim |  |
| `id_organizacao_destino` | bigint | sim |  |
| `organizacao_destino_nome` | text | sim |  |
| `tipo_organizacao_destino` | text | sim |  |
| `tipo_conexao` | text | sim |  |
| `data_inicio` | date | sim |  |
| `data_fim` | date | sim |  |
| `id_projeto` | bigint | sim |  |
| `valor_financeiro` | numeric | sim |  |
| `gerou_projeto` | boolean | sim |  |
| `gerou_contrato` | boolean | sim |  |
| `gerou_inovacao` | boolean | sim |  |


### `mart.fato_desempenho_organizacao`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `id_tempo` | bigint | sim |  |
| `faturamento` | numeric | sim |  |
| `numero_empregados` | integer | sim |  |
| `numero_empregados_tecnologia` | integer | sim |  |
| `exportacoes` | numeric | sim |  |
| `receita_produtos_novos` | numeric | sim |  |
| `investimento_p_d` | numeric | sim |  |
| `custos_reduzidos_por_inovacao` | numeric | sim |  |


### `mart.fato_inovacao`


Fato inovacao achatado: tecnologia principal em coluna (sem N:N) + lista textual de tecnologias relacionadas.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_inovacao` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `id_projeto` | bigint | sim |  |
| `nome` | text | sim |  |
| `descricao` | text | sim |  |
| `id_tipo_inovacao` | bigint | sim |  |
| `id_grau_novidade` | bigint | sim |  |
| `id_problema_alvo` | bigint | sim |  |
| `id_tecnologia_principal` | bigint | sim |  |
| `tecnologia_principal_nome` | text | sim |  |
| `tecnologias_relacionadas` | text | sim |  |
| `data_inicio` | date | sim |  |
| `data_implementacao` | date | sim |  |
| `status` | text | sim |  |
| `chegou_ao_mercado` | boolean | sim |  |
| `mercado_alvo` | text | sim |  |
| `impacto_trabalho` | text | sim |  |
| `receita_associada` | numeric | sim |  |
| `reducao_custo_estimada` | numeric | sim |  |
| `aumento_capacidade_percentual` | numeric | sim |  |
| `empregos_criados` | integer | sim |  |
| `empregos_qualificados_criados` | integer | sim |  |


### `mart.fato_investimento_inovacao`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `id_tempo` | bigint | sim |  |
| `id_fonte_recurso` | bigint | sim |  |
| `id_projeto` | bigint | sim |  |
| `categoria` | text | sim |  |
| `valor` | numeric | sim |  |
| `observacao` | text | sim |  |


### `mart.fato_propriedade_intelectual`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_pi` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `id_projeto` | bigint | sim |  |
| `tipo_pi` | text | sim |  |
| `titulo` | text | sim |  |
| `numero_registro` | text | sim |  |
| `data_deposito` | date | sim |  |
| `data_concessao` | date | sim |  |
| `status` | text | sim |  |
| `licenciada` | boolean | sim |  |
| `receita_licenciamento` | numeric | sim |  |


### `mart.fato_talento`


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fato` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `id_tempo` | bigint | sim |  |
| `pesquisadores_p_d` | integer | sim |  |
| `mestres` | integer | sim |  |
| `doutores` | integer | sim |  |
| `profissionais_stem` | integer | sim |  |
| `pessoas_capacitadas` | integer | sim |  |
| `novas_contratacoes_qualificadas` | integer | sim |  |


### `mart.universo_pesquisado`


Sampling frame de cada ciclo de coleta: organizacoes dentro do escopo, elegiveis ou nao.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `organizacao_nome` | text | sim |  |
| `elegivel` | boolean | sim |  |
| `motivo_inelegibilidade` | text | sim |  |


### `mart.vw_adocao_tecnologia`


Percentual de respondentes elegiveis (por ciclo de coleta) em cada nivel de adocao de cada tecnologia (0=declarou nao utilizar .. 4=critica). Organizacao nao-respondente ou fora do universo pesquisado nao aparece aqui.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | sim |  |
| `ciclo_coleta` | text | sim |  |
| `ano` | smallint | sim |  |
| `id_tecnologia` | bigint | sim |  |
| `tecnologia` | text | sim |  |
| `nivel_adocao` | smallint | sim |  |
| `qtd_organizacoes` | bigint | sim |  |
| `total_respondentes` | bigint | sim |  |
| `pct_organizacoes_respondentes` | numeric | sim |  |


### `mart.vw_bi_adocao_tecnologica`


Area 4 (adocao tecnologica): alias de mart.vw_adocao_tecnologia.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | sim |  |
| `ciclo_coleta` | text | sim |  |
| `ano` | smallint | sim |  |
| `id_tecnologia` | bigint | sim |  |
| `tecnologia` | text | sim |  |
| `nivel_adocao` | smallint | sim |  |
| `qtd_organizacoes` | bigint | sim |  |
| `total_respondentes` | bigint | sim |  |
| `pct_organizacoes_respondentes` | numeric | sim |  |


### `mart.vw_bi_empreendedorismo`


Area 9 (empreendedorismo e destruicao criativa): entrada de novas organizacoes/startups (data_entrada_ecossistema) e saidas registradas (data_saida_ecossistema) por ano. Para sobrevivencia por coorte, ver mart.vw_cohort_sobrevivencia_empresarial.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano` | smallint | sim |  |
| `novas_organizacoes` | bigint | sim |  |
| `novas_startups` | bigint | sim |  |
| `organizacoes_saidas` | bigint | sim |  |


### `mart.vw_bi_impacto_economico`


Area 8 (impacto economico): faturamento, exportacoes, reducao de custo e empregos gerados por ano.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano` | smallint | sim |  |
| `faturamento_total` | numeric | sim |  |
| `exportacoes_total` | numeric | sim |  |
| `custos_reduzidos_total` | numeric | sim |  |
| `receita_associada_total` | numeric | sim |  |
| `reducao_custo_estimada_total` | numeric | sim |  |
| `empregos_criados_total` | bigint | sim |  |
| `empregos_qualificados_criados_total` | bigint | sim |  |


### `mart.vw_bi_indicadores_municipio`


Area 2 (indicadores por municipio): organizacoes, investimento e inovacoes por municipio.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_municipio` | bigint | sim |  |
| `municipio` | text | sim |  |
| `uf` | character | sim |  |
| `pertence_area_atuacao` | boolean | sim |  |
| `qtd_organizacoes` | bigint | sim |  |
| `qtd_organizacoes_ativas` | bigint | sim |  |
| `investimento_total` | numeric | sim |  |
| `inovacoes_implementadas` | bigint | sim |  |


### `mart.vw_bi_indicadores_setor`


Area 3 (indicadores por setor): organizacoes, investimento e inovacoes por setor economico.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_setor` | bigint | sim |  |
| `setor` | text | sim |  |
| `qtd_organizacoes` | bigint | sim |  |
| `investimento_total` | numeric | sim |  |
| `inovacoes_implementadas` | bigint | sim |  |


### `mart.vw_bi_inovacao_grau_novidade`


Area 7 (inovacao e grau de novidade): alias de mart.vw_inovacao_por_grau_novidade.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_grau_novidade` | bigint | sim |  |
| `grau_novidade` | text | sim |  |
| `ordem` | smallint | sim |  |
| `qtd_inovacoes` | bigint | sim |  |
| `pct_inovacoes` | numeric | sim |  |


### `mart.vw_bi_pd_financiamento`


Area 5 (P&D e financiamento): intensidade de P&D por organizacao/ano. Combine com mart.vw_investimento_por_fonte para o detalhamento por fonte de recurso.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano` | smallint | sim |  |
| `id_organizacao` | bigint | sim |  |
| `investimento_p_d` | numeric | sim |  |
| `faturamento` | numeric | sim |  |
| `intensidade_p_d_pct` | numeric | sim |  |


### `mart.vw_bi_pipeline_inovacao`


Area 10 (pipeline de inovacao): funil de inovacoes por status (ideacao -> em_desenvolvimento -> piloto -> implementada/descontinuada).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `status` | text | sim |  |
| `qtd_inovacoes` | bigint | sim |  |
| `pct_inovacoes` | numeric | sim |  |


### `mart.vw_bi_rede_ecossistema`


Area 6 (rede do ecossistema): alias de mart.vw_rede_conexoes_por_tipo. Ver tambem mart.vw_rede_grau_organizacao e mart.vw_rede_densidade.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `tipo_origem` | text | sim |  |
| `tipo_destino` | text | sim |  |
| `tipo_conexao` | text | sim |  |
| `qtd_conexoes` | bigint | sim |  |
| `qtd_gerou_projeto` | bigint | sim |  |
| `qtd_gerou_contrato` | bigint | sim |  |
| `qtd_gerou_inovacao` | bigint | sim |  |


### `mart.vw_bi_visao_executiva`


Area 1 (visao executiva): principais indicadores do observatorio, por ano.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano` | smallint | sim |  |
| `empresas_acompanhadas` | bigint | sim |  |
| `investimento_total` | numeric | sim |  |
| `inovacoes_implementadas` | bigint | sim |  |
| `projetos_concluidos` | bigint | sim |  |
| `investimento_medio_por_inovacao` | numeric | sim |  |


### `mart.vw_cohort_sobrevivencia_empresarial`


Snapshot (nao serie temporal) de sobrevivencia por coorte de entrada no ecossistema: quantas organizacoes de cada ano de entrada ainda estao ativas hoje. Estrutura preparada para evoluir para uma curva de sobrevivencia completa quando houver snapshots periodicos de status.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano_coorte` | smallint | sim |  |
| `organizacoes_na_coorte` | bigint | sim |  |
| `organizacoes_ainda_ativas` | bigint | sim |  |
| `organizacoes_saidas` | bigint | sim |  |
| `taxa_sobrevivencia_atual_pct` | numeric | sim |  |
| `anos_medios_no_ecossistema` | numeric | sim |  |


### `mart.vw_conciliacao_investimento_pd`


Compara, por organizacao e ano, o P&D autodeclarado (fato_desempenho_organizacao.investimento_p_d) com a soma categorizada (fato_investimento_inovacao, categoria='p_d'). Divergencia grande pode indicar lancamento incompleto por categoria — nao e um erro de sistema, e uma diferenca esperada entre dois instrumentos de coleta distintos.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_organizacao` | bigint | sim |  |
| `ano` | smallint | sim |  |
| `investimento_p_d_autodeclarado` | numeric | sim |  |
| `investimento_p_d_categorizado` | numeric | sim |  |
| `diferenca` | numeric | sim |  |
| `diferenca_pct` | numeric | sim |  |


### `mart.vw_conversao_conexoes_projetos`


Percentual de conexoes do ecossistema que geraram projeto ou contrato.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `total_conexoes` | bigint | sim |  |
| `conexoes_com_resultado` | bigint | sim |  |
| `taxa_conversao_pct` | numeric | sim |  |


### `mart.vw_conversao_projetos_inovacao`


Percentual de projetos concluidos que geraram ao menos uma inovacao implementada.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `projetos_concluidos` | bigint | sim |  |
| `projetos_concluidos_com_inovacao` | bigint | sim |  |
| `taxa_conversao_pct` | numeric | sim |  |


### `mart.vw_inovacao_por_grau_novidade`


Quantidade e percentual de inovacoes por grau de novidade (empresa, regional, nacional, mundial).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_grau_novidade` | bigint | sim |  |
| `grau_novidade` | text | sim |  |
| `ordem` | smallint | sim |  |
| `qtd_inovacoes` | bigint | sim |  |
| `pct_inovacoes` | numeric | sim |  |


### `mart.vw_intensidade_p_d`


Intensidade de P&D: investimento_p_d / faturamento * 100, por organizacao e ano. Fonte de verdade para este KPI e core.fato_desempenho_organizacao.investimento_p_d (autodeclarado, mesmo grao do faturamento) — ver mart.vw_conciliacao_investimento_pd para comparar com o detalhamento categorizado.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_organizacao` | bigint | sim |  |
| `ano` | smallint | sim |  |
| `investimento_p_d` | numeric | sim |  |
| `faturamento` | numeric | sim |  |
| `intensidade_p_d_pct` | numeric | sim |  |


### `mart.vw_investimento_por_fonte`


Valor e percentual de investimento por fonte de recurso (proprio, FAPESC, FINEP, etc.).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_fonte_recurso` | bigint | sim |  |
| `fonte_recurso` | text | sim |  |
| `valor_total` | numeric | sim |  |
| `pct_investimento` | numeric | sim |  |


### `mart.vw_investimento_por_inovacao`


Investimento total em inovacao dividido pelo numero de inovacoes implementadas, por ano.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano` | smallint | sim |  |
| `total_investimento` | numeric | sim |  |
| `total_implementadas` | bigint | sim |  |
| `investimento_medio_por_inovacao` | numeric | sim |  |


### `mart.vw_investimento_por_setor`


Valor e percentual de investimento por setor economico da organizacao investidora.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_setor` | bigint | sim |  |
| `setor` | text | sim |  |
| `valor_total` | numeric | sim |  |
| `pct_investimento` | numeric | sim |  |


### `mart.vw_investimento_por_tecnologia`


Valor e percentual de investimento por tecnologia principal do projeto financiado (requer id_projeto preenchido no investimento).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_tecnologia` | bigint | sim |  |
| `tecnologia` | text | sim |  |
| `valor_total` | numeric | sim |  |
| `pct_investimento` | numeric | sim |  |


### `mart.vw_produtividade_trabalhador`


Faturamento por trabalhador (proxy de produtividade), por organizacao e ano.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_organizacao` | bigint | sim |  |
| `ano` | smallint | sim |  |
| `faturamento` | numeric | sim |  |
| `numero_empregados` | integer | sim |  |
| `produtividade_por_trabalhador` | numeric | sim |  |


### `mart.vw_receita_proveniente_inovacao`


Percentual do faturamento proveniente de produtos/servicos novos.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_organizacao` | bigint | sim |  |
| `ano` | smallint | sim |  |
| `receita_produtos_novos` | numeric | sim |  |
| `faturamento` | numeric | sim |  |
| `receita_proveniente_inovacao_pct` | numeric | sim |  |


### `mart.vw_rede_conexoes_por_tipo`


Conexoes agregadas por par de tipo de organizacao e tipo de conexao. Filtre tipo_origem/tipo_destino para ver empresa-universidade, empresa-ICT, empresa-startup etc.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `tipo_origem` | text | sim |  |
| `tipo_destino` | text | sim |  |
| `tipo_conexao` | text | sim |  |
| `qtd_conexoes` | bigint | sim |  |
| `qtd_gerou_projeto` | bigint | sim |  |
| `qtd_gerou_contrato` | bigint | sim |  |
| `qtd_gerou_inovacao` | bigint | sim |  |


### `mart.vw_rede_conversao`


Percentual de conexoes do ecossistema que se transformaram em projeto, contrato ou inovacao.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `total_conexoes` | bigint | sim |  |
| `qtd_gerou_projeto` | bigint | sim |  |
| `qtd_gerou_contrato` | bigint | sim |  |
| `qtd_gerou_inovacao` | bigint | sim |  |
| `pct_gerou_projeto` | numeric | sim |  |
| `pct_gerou_contrato` | numeric | sim |  |
| `pct_gerou_inovacao` | numeric | sim |  |


### `mart.vw_rede_densidade`


Densidade da rede = conexoes existentes / conexoes possiveis entre organizacoes ativas (grafo dirigido).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `total_organizacoes` | bigint | sim |  |
| `total_conexoes` | bigint | sim |  |
| `densidade_rede` | numeric | sim |  |


### `mart.vw_rede_grau_organizacao`


Grau de cada organizacao (numero de conexoes) e ranking de conectividade — base para "organizacoes mais conectadas".


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_organizacao` | bigint | sim |  |
| `nome` | text | sim |  |
| `tipo_organizacao` | text | sim |  |
| `grau` | bigint | sim |  |
| `ranking_conectividade` | bigint | sim |  |


### `mart.vw_respondentes_elegiveis`


Organizacoes elegiveis (universo_pesquisado) que efetivamente responderam (cobertura_coleta) em cada ciclo — base do denominador dos KPIs de cobertura.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `id_ciclo` | bigint | sim |  |
| `ano` | smallint | sim |  |
| `id_organizacao` | bigint | sim |  |


### `mart.vw_taxa_empresas_inovadoras`


Percentual de respondentes elegiveis (mart.vw_respondentes_elegiveis) com pelo menos uma inovacao implementada no ano. Requer ciclo_coleta/universo_pesquisado/cobertura_coleta preenchidos para o ano — sem isso, o ano nao aparece (nao ha "todas ativas" como fallback).


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano` | smallint | sim |  |
| `empresas_inovadoras` | bigint | sim |  |
| `empresas_respondentes` | bigint | sim |  |
| `taxa_empresas_inovadoras_pct` | numeric | sim |  |


### `mart.vw_taxa_primeira_inovacao`


Percentual de respondentes elegiveis do ano que implementaram sua PRIMEIRA inovacao naquele ano. Nao e uma medida de renovacao empresarial (entrada/saida de organizacoes) — para isso, ver mart.vw_cohort_sobrevivencia_empresarial.


| Coluna | Tipo | Nulo? | Descricao |
|---|---|---|---|
| `ano` | smallint | sim |  |
| `empresas_primeira_inovacao` | bigint | sim |  |
| `empresas_respondentes` | bigint | sim |  |
| `taxa_primeira_inovacao_pct` | numeric | sim |  |


---

Para regenerar este arquivo apos alterar o schema, rode a query abaixo (schemas `core`/`mart`) e reaplique o mesmo agrupamento por tabela:

```sql
SELECT c.table_schema, c.table_name,
       obj_description(format('%s.%s', c.table_schema, c.table_name)::regclass, 'pg_class'),
       c.ordinal_position, c.column_name, c.data_type, c.is_nullable,
       col_description(format('%s.%s', c.table_schema, c.table_name)::regclass, c.ordinal_position)
FROM information_schema.columns c
WHERE c.table_schema IN ('core','mart')
ORDER BY c.table_schema, c.table_name, c.ordinal_position;
```
