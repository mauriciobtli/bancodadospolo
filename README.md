# Banco de Dados de Inovacao do Polo Inovale

Data Warehouse PostgreSQL do Observatorio de Inovacao e Desenvolvimento
Economico do Polo Inovale. Mede a transformacao de recursos e conhecimento
em inovacao e resultados economicos — nao apenas as atividades do
ecossistema — cobrindo capital humano, P&D, conexoes do ecossistema,
producao de inovacao, empreendedorismo, adocao tecnologica, impacto
economico e direcionalidade da inovacao. Consumido principalmente pelo
Power BI.

## Arquitetura

```text
raw   -> pouso de dados brutos (CSV/XLSX/Sheets), tipagem fraca (texto)
core  -> dados limpos, deduplicados, normalizados, com integridade referencial
mart  -> modelo dimensional e views/KPIs consumidos pelo Power BI
etl   -> controle de carga (etl_execucao) e quarentena de registros invalidos
app   -> tabelas internas do admin web (Django) — usuarios, sessoes, grupos
```

`app` é gerido só por `manage.py migrate` (Django), nunca pelo Alembic — é
infraestrutura para o consumidor "admin web" (`webapp/`), não faz parte do
modelo do DW em si. Ver [`webapp/README.md`](webapp/README.md).

Toda logica de negocio relevante (KPIs, agregados) vive como SQL view no
banco — o Power BI so consome `mart`, nunca recalcula metricas com lógica
propria. Veja o modelo completo em [`docs/modelo_er.md`](docs/modelo_er.md)
(diagrama Mermaid) e [`docs/views_e_kpis.md`](docs/views_e_kpis.md)
(formula de cada KPI).

### Estrutura de pastas

```text
db/
  migrations/   # Alembic — versiona e aplica o DDL abaixo, em ordem
  schemas/      # DDL de referencia (schemas, funcoes, tabelas, views), lido pelas migrations
  seeds/        # seed idempotente das dimensoes fixas
  roles/        # role read-only do Power BI
etl/
  loaders/      # CSV, XLSX, Google Sheets -> raw.*
  transforms/   # normalizacao de texto/nome/data, deduplicacao de organizacoes
  validators/   # CNPJ, dominios (enums)
  pipeline.py   # orquestracao raw -> core (ex.: organizacoes)
  execucao.py   # etl_execucao / quarentena
tests/
  db/     # integridade (PK/FK, dominios, valores negativos, datas)
  etl/    # validadores, transformacoes, pipeline ponta a ponta
  mart/   # KPIs (divisao por zero)
docs/     # dicionario de dados, ER, views/KPIs, backup/restore
data/samples/  # CSV de exemplo (sem dados reais) para testar o loader
webapp/   # admin web (Django) — cadastro/consulta/edicao/importacao, ver webapp/README.md
```

## Seguranca de dados

- **Nenhuma credencial vive no repositorio.** `.env` esta no `.gitignore`;
  use `.env.example` como modelo.
- **Role dedicada e read-only para o Power BI** (`powerbi_readonly`), com
  `GRANT` restrito ao schema `mart`. Sem acesso a `raw`, `core` ou `etl` —
  verificado em `db/roles/powerbi_readonly.sql` e coberto por teste manual
  (ver "Como validamos" abaixo).
- **Dados pessoais isolados**: `core.contato_organizacao` (nome de contato,
  e-mail, telefone) fica fora do schema `mart` e fora do grant da role de
  leitura. `dim_organizacao`/`mart.dim_organizacao` tem apenas dados
  publicos/institucionais (CNPJ, nome, site). No admin web (`webapp/`),
  o acesso a `contato_organizacao` fica restrito ao grupo Django
  "Contatos" — nenhum outro grupo (nem "Leitura") enxerga esse dado, em
  nenhuma tela (verificado manualmente: 403 em acesso direto por URL).
- **Role dedicada para o admin web** (`django_app`, ver
  `db/roles/django_app.sql`): leitura/escrita em `core`, leitura em `etl`,
  sem acesso a `raw`/`mart`. A gravacao em `raw`/`etl` durante uma
  importacao pela tela web usa a role de administracao do ETL, nao
  `django_app` — ver [`webapp/README.md`](webapp/README.md).
- **Dumps de backup nunca sao commitados** (`db_backups/*.dump` no
  `.gitignore`) — contem dados pessoais. Ver
  [`docs/backup_restore.md`](docs/backup_restore.md).
- **Quarentena em vez de descarte silencioso**: registros invalidos vao
  para `etl.quarentena_registro` (JSON + motivo), nunca sao perdidos nem
  inseridos sem validacao.

## Instalacao

Pre-requisitos: Python 3.11+, PostgreSQL 16 acessivel (local, Docker ou
gerenciado).

```bash
git clone <repo>
cd bancodadospolo
cp .env.example .env
# edite .env com host/porta/usuario/senha do seu Postgres

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Banco via Docker (opcional)

```bash
docker compose up -d
```

Isso sobe um Postgres 16 usando as credenciais do `.env`
(`POLO_DB_USER`/`POLO_DB_PASSWORD`/`POLO_DB_NAME`). Se preferir um Postgres
ja existente, so aponte `POLO_DB_HOST`/`POLO_DB_PORT` no `.env` e pule esta
etapa — o restante do fluxo e identico.

### Migrations (schema completo: schemas, tabelas, seeds, views, role)

```bash
alembic upgrade head
```

As 4 migrations sao aplicadas em ordem e sao idempotentes (podem ser
reexecutadas): `0001` (schemas/funcoes/raw/core), `0002` (seed das
dimensoes fixas), `0003` (views do `mart`), `0004` (role
`powerbi_readonly`).

Depois da primeira aplicacao, defina a senha da role de leitura (nunca via
SQL versionado — ver comentario em `db/roles/powerbi_readonly.sql`):

```bash
psql -h "$POLO_DB_HOST" -U "$POLO_DB_USER" -d "$POLO_DB_NAME" \
  -c "ALTER ROLE powerbi_readonly WITH PASSWORD '<gere uma senha forte>';"
```

Guarde essa senha em um cofre de segredos (nunca no `.env` versionado —
`POLO_BI_DB_PASSWORD` no `.env.example` e so um placeholder local).

### Rodar os testes

```bash
pytest
```

Os testes de `tests/db` e `tests/mart` exigem o Postgres com as migrations
aplicadas (usam a mesma conexao do `.env`); rodam dentro de uma transacao
revertida ao final, entao nao deixam dado residual. Os testes de
`tests/etl/test_cnpj.py`, `test_normalizacao.py` e `test_dedup.py` sao
unitarios (sem banco).

### Como validamos este entregavel

Antes de commitar, o schema completo foi aplicado (`alembic upgrade head`)
em um Postgres 16 real, com:

- as 53 views de `mart` testadas com `SELECT ... LIMIT 1` (sem erro, inclusive
  com banco vazio — confirma que `NULLIF` evita divisao por zero em todos os KPIs);
- a role `powerbi_readonly` testada de fato: consegue `SELECT` em `mart`,
  recebe `permission denied` em `core`/`etl`, e nao consegue escrever em
  `mart` (views nao atualizaveis);
- `alembic downgrade base` seguido de `alembic upgrade head` (ciclo
  completo de reconstrucao) sem erros;
- suite de testes completa (`pytest`) passando.

## Carga de dados (ETL)

Fluxo de referencia totalmente implementado para organizacoes — os demais
loaders (investimentos, inovacoes, conexoes etc.) seguem o mesmo padrao em
`etl/loaders/csv_loader.py` / `xlsx_loader.py` (genericos, por mapeamento
de colunas) + uma funcao `processar_<entidade>` analoga a
`processar_organizacoes` em `etl/pipeline.py`.

```python
from sqlalchemy import create_engine
from etl.config import build_database_url
from etl.pipeline import carregar_organizacoes_csv, processar_organizacoes
from pathlib import Path

engine = create_engine(build_database_url(readonly=False))
with engine.begin() as conn:  # commit automatico ao sair do bloco sem erro
    execucao = carregar_organizacoes_csv(conn, Path("data/samples/organizacoes_exemplo.csv"))
    processar_organizacoes(conn, execucao)
    execucao.finalizar(status="sucesso_parcial" if execucao.registros_rejeitados else "sucesso")

print(f"lidos={execucao.registros_lidos} inseridos={execucao.registros_inseridos} "
      f"atualizados={execucao.registros_atualizados} rejeitados={execucao.registros_rejeitados}")
```

O pipeline de organizacoes cobre: validacao de CNPJ (digito verificador),
normalizacao de nome/texto/booleanos, tratamento tolerante de datas
(formatos BR e ISO), deduplicacao (CNPJ valido como chave primaria; nome
normalizado + municipio como fallback) e quarentena de linhas invalidas em
`etl.quarentena_registro`, com contadores agregados em `etl.etl_execucao`.

### Google Sheets

`etl/loaders/gsheets_loader.py` funciona hoje para planilhas publicadas na
web como CSV (Planilhas Google > Arquivo > Compartilhar > Publicar na web).
Para planilhas privadas, o ponto de extensao esta documentado no proprio
arquivo (service account via `POLO_GSHEETS_CREDENTIALS_FILE`, ja reservado
no `.env.example`) — nao implementado nesta primeira versao para evitar
dependencia (`gspread`) sem uso imediato.

## Regras de negocio

- **Historico nunca e sobrescrito.** Fatos periodicos (desempenho, talento,
  adocao tecnologica) tem `UNIQUE (organizacao, periodo, ...)`: uma
  correcao dentro do mesmo periodo faz upsert; um novo periodo sempre gera
  uma linha nova. Um ano fechado nunca e substituido pelo valor de outro
  ano.
- **Dimensoes fixas sao seedadas por codigo natural** (`ON CONFLICT
  (codigo) DO NOTHING`), nunca hardcoded no ETL.
- **`core.projeto.valor_total` e orcado/planejado**; o investimento
  efetivamente realizado e a soma de `core.fato_investimento_inovacao`
  (exposta via `mart.vw_investimento_por_inovacao` e correlatas) — os dois
  numeros podem divergir por design.
- **CNPJ e opcional.** Organizacoes sem CNPJ (coletivos, grupos de
  pesquisa informais) sao aceitas; a deduplicacao cai para nome normalizado
  + municipio nesse caso.
- Demais decisoes de modelagem (o que virou FK, o que ficou como enum
  simples) estao documentadas em
  [`docs/modelo_er.md`](docs/modelo_er.md#decisões-de-modelagem-que-se-afastam-do-texto-literal-do-briefing).
- **Universo pesquisado / cobertura de coleta** (`core.ciclo_coleta`,
  `core.universo_pesquisado`, `core.cobertura_coleta`): ausencia de dado
  NAO significa "zero" — distingue organizacao fora do escopo, organizacao
  que nao respondeu, e organizacao que respondeu e declarou explicitamente
  nao usar uma tecnologia. `vw_taxa_empresas_inovadoras`, `vw_taxa_primeira_inovacao`
  e `vw_adocao_tecnologia` usam `mart.vw_respondentes_elegiveis` como
  denominador — ver [`docs/views_e_kpis.md`](docs/views_e_kpis.md).
- **Investimento em P&D tem fonte de verdade documentada** para evitar duas
  metricas divergentes: `fato_desempenho_organizacao.investimento_p_d`
  (autodeclarado) para o KPI de intensidade, `fato_investimento_inovacao`
  categorizado para o detalhamento por fonte/tecnologia/setor. Nunca somar
  as duas — ver `mart.vw_conciliacao_investimento_pd`.
- **Idempotencia de cargas**: `fato_inovacao`, `fato_conexao_ecossistema` e
  `fato_propriedade_intelectual` (as unicas tabelas fato sem chave natural
  de grao) ganharam `id_origem_externa` + indice unico parcial, permitindo
  `ON CONFLICT (id_origem_externa) DO UPDATE` em reprocessamentos.

## Pendencias conhecidas / proximos passos

- `core.dim_municipio` ja cobre os 12 municipios oficiais da area de
  atuacao (AMMOC); os codigos IBGE foram conferidos por multiplas fontes
  mas vale uma confirmacao final contra a tabela oficial do IBGE antes de
  producao (ver comentario no topo da secao de municipios em
  `db/seeds/seed_dimensoes.sql`).
- Loaders de `investimentos`, `inovacoes`, `conexoes`, `adocao_tecnologica`,
  `desempenho_organizacao`, `talento` e `propriedade_intelectual` ainda nao
  tem uma funcao `processar_<entidade>` implementada (so a tabela `raw.*` e
  o loader generico existem) — seguir o padrao de
  `etl/pipeline.py::processar_organizacoes`.
- Analise de rede avancada (centralidade, deteccao de comunidades) fica
  para uma proxima fase; o modelo relacional ja suporta.
- `mart.vw_cohort_sobrevivencia_empresarial` e um snapshot do estado atual,
  nao uma curva de sobrevivencia por periodo — evoluir quando houver
  snapshots periodicos de status das organizacoes.

## Documentacao complementar

- [`docs/modelo_er.md`](docs/modelo_er.md) — diagrama ER completo (Mermaid) e decisoes de modelagem
- [`docs/dicionario_de_dados.md`](docs/dicionario_de_dados.md) — todas as tabelas/colunas de `core` e `mart`, geradas do banco real
- [`docs/views_e_kpis.md`](docs/views_e_kpis.md) — formula de cada KPI, exemplos de consulta
- [`docs/backup_restore.md`](docs/backup_restore.md) — `pg_dump`/`pg_restore`, cuidados com dados pessoais
