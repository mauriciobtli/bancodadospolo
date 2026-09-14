# Backup e restore

## Backup

Use `pg_dump` no formato custom (`-Fc`), que permite restore seletivo e e
mais compacto que SQL puro. Rode como o usuario admin (`POLO_DB_USER`),
nunca como a role `powerbi_readonly` (que nem teria permissao de ler
`raw`/`core`/`etl`).

```bash
set -a; source .env; set +a

mkdir -p db_backups
PGPASSWORD="$POLO_DB_PASSWORD" pg_dump \
  -h "$POLO_DB_HOST" -p "$POLO_DB_PORT" -U "$POLO_DB_USER" \
  -Fc -f "db_backups/polo_inovale_$(date +%Y%m%d_%H%M).dump" \
  "$POLO_DB_NAME"
```

`db_backups/*.dump` esta no `.gitignore` — dumps contem dados reais
(incluindo `core.contato_organizacao`, com dados pessoais) e **nunca devem
ser commitados**.

### Backup so do schema (sem dados) — util para revisao de estrutura

```bash
PGPASSWORD="$POLO_DB_PASSWORD" pg_dump \
  -h "$POLO_DB_HOST" -p "$POLO_DB_PORT" -U "$POLO_DB_USER" \
  --schema-only -f "db_backups/schema_$(date +%Y%m%d).sql" \
  "$POLO_DB_NAME"
```

## Restore

### Restaurar um dump completo em um banco novo/vazio

```bash
set -a; source .env; set +a

PGPASSWORD="$POLO_DB_PASSWORD" createdb \
  -h "$POLO_DB_HOST" -p "$POLO_DB_PORT" -U "$POLO_DB_USER" "$POLO_DB_NAME"

PGPASSWORD="$POLO_DB_PASSWORD" pg_restore \
  -h "$POLO_DB_HOST" -p "$POLO_DB_PORT" -U "$POLO_DB_USER" \
  -d "$POLO_DB_NAME" --no-owner --no-privileges \
  db_backups/polo_inovale_AAAAMMDD_HHMM.dump
```

Apos o restore, reaplique a role read-only (o dump nao inclui a senha, por
seguranca — `pg_dump` nunca exporta credenciais):

```bash
alembic stamp head   # garante que o alembic_version bate com o schema restaurado
psql -h "$POLO_DB_HOST" -U "$POLO_DB_USER" -d "$POLO_DB_NAME" \
  -c "ALTER ROLE powerbi_readonly WITH PASSWORD '<senha do cofre de segredos>';"
```

### Reconstruir do zero (sem dump — ambiente novo)

Quando nao ha dump disponivel (ex.: ambiente de desenvolvimento), reconstrua
so com as migrations + seeds (sem dados de producao):

```bash
alembic upgrade head
```

## Recomendacoes operacionais

- Agende backups automaticos (cron/CI) com retenção definida (ex.: diario
  por 14 dias, semanal por 3 meses) — nao ha automacao de agendamento neste
  repositorio, apenas os comandos manuais acima.
- Teste o restore periodicamente em um banco descartavel — um backup nunca
  testado e um backup que nao existe.
- Trate qualquer dump com o mesmo cuidado de um segredo: contem
  `core.contato_organizacao` (dados pessoais). Nao envie por canais
  inseguros (e-mail, chat sem criptografia) nem deixe em disco
  compartilhado sem controle de acesso.
