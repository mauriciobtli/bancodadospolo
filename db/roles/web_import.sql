-- =========================================================================
-- Role dedicada e minima para a IMPORTACAO disparada pela tela web
-- (webapp/importacao/views.py), separada da role de administracao do ETL
-- (POLO_DB_USER) e da role do Django Admin (django_app).
--
-- Por que uma terceira role: o processo web e o unico ponto do sistema
-- exposto a upload de arquivo por um usuario autenticado via navegador —
-- se ele rodasse com a role de administracao (POLO_DB_USER, dona de todo o
-- schema, com DDL), qualquer falha na aplicacao (bug, dependencia
-- comprometida, etc.) teria alcance total sobre o banco. web_import so
-- pode fazer exatamente o que etl/pipeline.py::processar_organizacoes (e
-- os loaders que o alimentam) precisam: gravar a linha bruta em raw,
-- ler/gravar as dimensoes/fatos de core que o pipeline toca, e
-- ler/gravar o controle de execucao/quarentena em etl. Nunca DDL, nunca
-- DELETE, nunca schema app (tabelas internas do Django) nem mart
-- (exclusivo do Power BI).
--
-- Privilegios de web_import:
--   raw  -> leitura e escrita (landing dos arquivos importados).
--   core -> leitura e escrita, sem DELETE (o pipeline so insere/atualiza
--           dimensoes/fatos; nunca apaga linha existente).
--   etl  -> leitura e escrita, sem DELETE (grava etl_execucao e
--           quarentena_registro; nunca apaga historico).
--   app  -> sem acesso (tabelas internas do Django; geridas por
--           manage.py migrate com a role django_app).
--   mart -> sem acesso (exclusivo do Power BI via powerbi_readonly).
-- =========================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'web_import') THEN
        CREATE ROLE web_import WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
            CONNECTION LIMIT 10;
    END IF;
END
$$;

COMMENT ON ROLE web_import IS 'Role de servico da tela de importacao do admin web (privilegio minimo: raw+core+etl, sem DELETE, sem DDL, sem acesso a app/mart). Nunca usar POLO_DB_USER dentro do processo web.';

-- Nunca definir senha aqui (mesma politica de powerbi_readonly/django_app):
-- rode este script e defina a senha manualmente, guardando-a num cofre de
-- segredos.

GRANT USAGE ON SCHEMA raw TO web_import;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA raw TO web_import;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO web_import;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT, INSERT, UPDATE ON TABLES TO web_import;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT USAGE, SELECT ON SEQUENCES TO web_import;

GRANT USAGE ON SCHEMA core TO web_import;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA core TO web_import;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO web_import;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT SELECT, INSERT, UPDATE ON TABLES TO web_import;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO web_import;

GRANT USAGE ON SCHEMA etl TO web_import;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA etl TO web_import;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA etl TO web_import;
ALTER DEFAULT PRIVILEGES IN SCHEMA etl GRANT SELECT, INSERT, UPDATE ON TABLES TO web_import;
ALTER DEFAULT PRIVILEGES IN SCHEMA etl GRANT USAGE, SELECT ON SEQUENCES TO web_import;

-- Bloqueios explicitos (documentam a intencao, alem de ja serem o padrao
-- para uma role recem-criada sem GRANT nesses schemas).
REVOKE ALL ON SCHEMA public FROM web_import;
REVOKE ALL ON SCHEMA app FROM web_import;
REVOKE ALL ON SCHEMA mart FROM web_import;
