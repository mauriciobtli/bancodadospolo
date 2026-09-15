-- =========================================================================
-- Schema e role para a camada administrativa web (Django).
--
-- Django ganha um schema proprio (`app`) para suas tabelas internas
-- (usuarios, sessoes, grupos, permissoes, log do admin, controle de
-- migrations do Django) — nunca toca em raw/core/mart/etl, que continuam
-- geridas exclusivamente pelo Alembic (ver db/migrations). "V1 do DW
-- aprovada": esta migration NAO altera nenhuma tabela existente, so
-- adiciona infraestrutura para um novo consumidor (o admin web),
-- seguindo o mesmo padrao ja usado para powerbi_readonly.
--
-- Privilegios de django_app:
--   app  -> dono efetivo (USAGE + CREATE), e onde o Django gerencia seu
--           proprio schema via manage.py migrate.
--   core -> leitura e escrita (e o cadastro operacional que o admin web edita).
--   etl  -> somente leitura (telas de acompanhamento de execucao/quarentena).
--   raw  -> sem acesso. A gravacao em raw/etl durante uma importacao
--           disparada pela tela web continua sendo feita pela role de
--           administracao do ETL (POLO_DB_USER), nao por django_app — o
--           mesmo caminho de codigo (etl/pipeline.py) usado pelo ETL de
--           linha de comando, so que acionado por um botao na web.
--   mart -> sem acesso (exclusivo do Power BI via powerbi_readonly).
-- =========================================================================

CREATE SCHEMA IF NOT EXISTS app;
COMMENT ON SCHEMA app IS 'Tabelas internas do Django (usuarios, sessoes, grupos, permissoes, log de admin). Gerido por manage.py migrate, nunca pelo Alembic.';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'django_app') THEN
        CREATE ROLE django_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
            CONNECTION LIMIT 20;
    END IF;
END
$$;

COMMENT ON ROLE django_app IS 'Role de servico da aplicacao administrativa Django. Leitura/escrita em core e app; leitura em etl; sem acesso a raw/mart.';

-- Nunca definir senha aqui (mesma politica de powerbi_readonly): rode este
-- script e defina a senha manualmente, guardando-a num cofre de segredos.

GRANT USAGE, CREATE ON SCHEMA app TO django_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON TABLES TO django_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON SEQUENCES TO django_app;

GRANT USAGE ON SCHEMA core TO django_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO django_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO django_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO django_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO django_app;

GRANT USAGE ON SCHEMA etl TO django_app;
GRANT SELECT ON ALL TABLES IN SCHEMA etl TO django_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA etl GRANT SELECT ON TABLES TO django_app;

-- Bloqueios explicitos (documentam a intencao, alem de ja serem o padrao
-- para uma role recem-criada sem GRANT nesses schemas).
REVOKE ALL ON SCHEMA public FROM django_app;
REVOKE ALL ON SCHEMA raw FROM django_app;
REVOKE ALL ON SCHEMA mart FROM django_app;
