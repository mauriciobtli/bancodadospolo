# Admin web do Polo Inovale

Camada administrativa (Django + Django Admin) para cadastrar, consultar,
editar e importar dados no Data Warehouse do Polo Inovale. Não é uma
aplicação Django "cheia" — é o Django Admin customizado, conectado
diretamente ao schema `core` do banco já existente (ver `../README.md` e
`../docs/` para o modelo de dados).

## Princípios

- **O Postgres continua sendo a fonte de verdade das regras de negócio.**
  Este app não reimplementa CHECK constraints, triggers de sincronização
  (líder/tecnologia principal do projeto) nem a lógica de
  validação/deduplicação do ETL — ele reaproveita o pacote `etl/` já
  existente (mesmo código, mesmos testes) e deixa o banco rejeitar o que
  for inválido, traduzindo a mensagem de erro para o usuário quando isso
  acontece.
- **`core` é a camada operacional; `mart` continua exclusiva do Power BI.**
  Este app lê/escreve em `core` (e lê `etl` para acompanhar importações) —
  nunca toca em `mart`.
- **Simplicidade de uso, não aparência.** Tema padrão do Django Admin, só
  com marca/idioma ajustados.

## Arquitetura

```
Funcionário → Django Admin (webapp/, role django_app) → Postgres (core: leitura/escrita, etl: leitura)
Power BI    → mart (role powerbi_readonly, inalterado)
```

- Os modelos que representam tabelas de `core.*`/`etl.*` são
  **`managed = False`**: o Django só os descreve para gerar
  formulários/consultas — quem cria/altera essas tabelas continua sendo o
  Alembic (`../db/migrations`).
- O Django tem seu **próprio schema Postgres (`app`)** para as tabelas
  internas (usuários, sessões, grupos, permissões, log do admin) — criado
  pela migration `0005_django_app_role` do Alembic
  (`../db/roles/django_app.sql`). `manage.py migrate` nunca toca em
  `raw`/`core`/`mart`/`etl`.
- Role dedicada **`django_app`**: leitura/escrita em `core`, leitura em
  `etl`, sem acesso a `raw`/`mart`. A importação de arquivos (que grava em
  `raw`/`etl`) roda com uma **terceira role, também dedicada e mínima,
  `web_import`** (`etl.db.get_web_import_engine()`, mesmo caminho de
  código — `etl/pipeline.py` — do ETL de linha de comando), nunca com
  `django_app` nem com a role de administração (`POLO_DB_USER`): o
  processo web é o único ponto do sistema exposto a upload de arquivo por
  um usuário autenticado via navegador, então roda com o menor
  privilégio possível — leitura/escrita em `raw`/`core`/`etl`, sem
  `DELETE`, sem DDL, sem acesso a `app`/`mart` (ver
  `db/roles/web_import.sql`).

## Perfis de usuário (grupos Django)

Criados automaticamente por `manage.py migrate` (migration
`core_admin.0001_initial`):

| Grupo | Acesso |
|---|---|
| **Cadastro** | CRUD completo em tudo, exceto contatos das organizações |
| **Contatos** | Acesso a `ContatoOrganizacao` (dado pessoal/LGPD) — some para quem não está neste grupo, inclusive a aba inline em Organização |
| **Importação** | Acesso à tela de importação CSV/XLSX (permissão nomeada à parte, por ser uma ação de maior impacto) |
| **Leitura** | Só visualização, em tudo exceto contatos |

Superusuários (`createsuperuser`) têm acesso total, incluindo gestão de
usuários/grupos.

## Instalação

```bash
cd ..  # raiz do repositório
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,webapp]"
```

### Banco: roles e schema do Django

```bash
alembic upgrade head   # aplica, entre outras, as migrations 0005 (schema app + role django_app)
                        # e 0006 (role web_import, para a tela de importação)
psql -h "$POLO_DB_HOST" -U "$POLO_DB_USER" -d "$POLO_DB_NAME" \
  -c "ALTER ROLE django_app WITH PASSWORD '<gere uma senha forte>';"
psql -h "$POLO_DB_HOST" -U "$POLO_DB_USER" -d "$POLO_DB_NAME" \
  -c "ALTER ROLE web_import WITH PASSWORD '<gere outra senha forte>';"
```

### Variáveis de ambiente

Acrescente ao `.env` da raiz do repositório (ver `.env.example`):
`DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`, `DJANGO_SECRET_KEY`,
`DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`,
`WEB_IMPORT_DB_USER`, `WEB_IMPORT_DB_PASSWORD`.

Gere a `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Migrations do Django (só tabelas internas: usuários, sessões, grupos)

```bash
python webapp/manage.py migrate
python webapp/manage.py createsuperuser
```

### Rodar localmente

```bash
python webapp/manage.py runserver
```

Acesse `http://127.0.0.1:8000/` (o admin fica na raiz do site, não em
`/admin/`) e faça login com o superusuário criado.

## Telas

- **Organizações** — cadastro, busca por nome/CNPJ/município/setor, aba
  "Contatos" (restrita).
- **Projetos** — cadastro com abas "Participantes" (papel funcional —
  "líder" não é uma opção aqui, é definido pelo campo "Organização líder"
  do projeto) e "Tecnologias do projeto" (idem para "principal").
- **Inovação, Financeiro, Ecossistema, Adoção Tecnológica, Desempenho e
  Talentos, Propriedade Intelectual** — CRUD padrão. Os fatos anuais
  (desempenho, talentos, investimento, adoção tecnológica) mostram um
  campo simples "Ano de referência" em vez do identificador técnico de
  data — internamente resolvido para 31/12 daquele ano, a mesma convenção
  já usada no DW.
- **Pesquisa (Ciclos de Coleta)** — ciclo com abas "Universo pesquisado" e
  "Cobertura de coleta" (não têm tela própria: PK composta no banco não é
  suportada pelo registro padrão do Django Admin — geridas só como aba do
  ciclo). Ação em massa "Adicionar organizações ativas da área de atuação
  ao universo pesquisado".
- **Importação** — upload de CSV/XLSX de organizações, reaproveitando
  `etl/loaders` e `etl/pipeline` (mesmo código testado do ETL de linha de
  comando). Mostra o resultado (lidos/inseridos/atualizados/rejeitados) e
  linka para o histórico de execuções e a quarentena. Novas entidades
  seguem o mesmo padrão (`etl/pipeline.py::processar_<entidade>`).

## Testes automatizados

```bash
cd webapp
pytest    # usa webapp/pytest.ini (DJANGO_SETTINGS_MODULE=config.settings)
```

**Estratégia de banco de teste (separada da suíte do Data Warehouse, e
documentada aqui de propósito):** os testes rodam DIRETO contra o mesmo
Postgres de desenvolvimento/CI já provisionado (`alembic upgrade head` +
`python manage.py migrate` já aplicados), usando a role real `django_app`
configurada em `DATABASES` — nunca uma role com `CREATEDB`. Isso é feito
sobrescrevendo a fixture `django_db_setup` do pytest-django em
`webapp/conftest.py` para não criar/apagar um banco de teste via `CREATE
DATABASE`/`DROP DATABASE` (o comportamento padrão do Django, que exigiria
`CREATEDB` da role usada). Cada teste que toca o banco roda dentro de uma
transação revertida ao final (fixture `db`/marcador `@pytest.mark.django_db`
do pytest-django), então nenhum teste deixa dado residual — o mesmo padrão
já usado por `../tests/conftest.py` (a suíte do Data Warehouse) no mesmo
Postgres. Isso também dá mais fidelidade ao teste: ele roda com a mesma
role de privilégio mínimo usada em produção, então qualquer dependência
indevida de um privilégio que `django_app` não tem aparece como uma
falha real de teste.

Duas exceções à transação automática, ambas com limpeza manual no
teardown da própria fixture:
- Fixtures que gravam em `etl.*`/`raw.*` usam uma conexão separada (a
  role de administração do ETL, `etl.db.get_engine()`), pois
  `django_app` só tem `SELECT` nesses schemas (ver
  `db/roles/django_app.sql`) — mesmo caminho de escrita real de
  produção (`tests/test_quarentena_pii.py`).
- O teste de upload real (`tests/test_importacao.py`) sobe um CSV pela
  tela web, que grava via a role `web_import` (conexão SQLAlchemy
  separada da conexão Django) — também limpo manualmente no teardown.

Cobertura: permissões dos 4 grupos (`test_permissoes.py`), mascaramento
de PII na quarentena (`test_quarentena_pii.py`), autorização de
importação e a role usada para gravar (`test_importacao.py`), campo "Ano
de referência" em criação/edição (`test_ano_referencia.py`), CRUD de
organização (`test_organizacao_crud.py`), sincronização das bridges de
projeto (`test_projeto_bridge.py`) e ciclos de coleta com PK composta
(`test_ciclo_coleta.py`).

## O que foi validado manualmente (Postgres real, sessão de desenvolvimento)

- Login, branding, agrupamento de menu por tema.
- CRUD de organização com validação de CNPJ e aba de contato.
- Importação real do CSV de exemplo pela tela web (3 inseridas, 2 rejeitadas
  e visíveis na quarentena).
- Isolamento de PII: usuário só no grupo "Cadastro" não vê `ContatoOrganizacao`
  em lugar nenhum (formulário, menu, nem acesso direto por URL — 403).
- Campo "Ano de referência" gravando corretamente em `dim_tempo` (31/12).
- Erro de banco (`UNIQUE`/`CHECK`/trigger de guarda) mostrado como mensagem
  amigável, sem página 500 — testado com uma duplicidade real de
  `fato_desempenho_organizacao`.
- Criação de projeto com líder pela tela web sincronizando
  `bridge_projeto_organizacao` automaticamente (trigger do banco), e o
  papel "líder" corretamente ausente das opções da aba de participantes.

## Pendências conhecidas

- Import CSV/XLSX implementado só para organizações; demais entidades
  seguem o padrão já estabelecido em `etl/pipeline.py`.
- `mart.vw_cohort_sobrevivencia_empresarial` e outras views analíticas
  continuam exclusivas do Power BI — não há tela de relatório no admin web
  (fora de escopo: o admin é para cadastro/operação, não para análise).
