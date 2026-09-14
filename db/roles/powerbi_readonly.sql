-- =========================================================================
-- Role de leitura para o Power BI.
-- Acesso SOMENTE ao schema mart. Sem acesso a raw, core ou etl — isso
-- inclui core.contato_organizacao (dados pessoais) e etl.etl_execucao
-- (pode conter caminhos de arquivo/mensagens de erro internas).
--
-- A senha NUNCA deve ser definida neste arquivo. Rode este script e em
-- seguida defina a senha manualmente (psql \password ou ALTER ROLE ...
-- PASSWORD via variavel de ambiente), ou gere a role via variavel no seu
-- gerenciador de segredos. Nunca commite a senha no repositorio.
-- =========================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'powerbi_readonly') THEN
        CREATE ROLE powerbi_readonly WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
            CONNECTION LIMIT 10;
    END IF;
END
$$;

COMMENT ON ROLE powerbi_readonly IS 'Role read-only usada pelo Power BI. Acesso restrito ao schema mart.';

-- Nunca permitir criar objetos no schema public por engano.
REVOKE ALL ON SCHEMA public FROM powerbi_readonly;

-- Bloqueia explicitamente qualquer acesso a schemas sensiveis.
REVOKE ALL ON SCHEMA raw FROM powerbi_readonly;
REVOKE ALL ON SCHEMA core FROM powerbi_readonly;
REVOKE ALL ON SCHEMA etl FROM powerbi_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA raw FROM powerbi_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA core FROM powerbi_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA etl FROM powerbi_readonly;

-- Acesso somente leitura ao schema mart.
DO $$
BEGIN
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO powerbi_readonly', current_database());
END
$$;

GRANT USAGE ON SCHEMA mart TO powerbi_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO powerbi_readonly;

-- Garante que views/materialized views criadas no futuro no schema mart
-- ja nascem com SELECT liberado para a role, sem precisar de novo GRANT manual.
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO powerbi_readonly;
