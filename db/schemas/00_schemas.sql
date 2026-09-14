-- Schemas do Data Warehouse do Polo Inovale.
-- raw  : pouso de dados brutos, tipagem fraca, 1:1 com a fonte original.
-- etl  : controle de carga (execuções, quarentena) — nunca exposto ao Power BI.
-- core : dados limpos, deduplicados, normalizados, com integridade referencial.
-- mart : modelo dimensional e views analíticas consumidas pelo Power BI.

-- Usada na deduplicacao de organizacoes sem CNPJ (comparacao de nomes sem acento).
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS etl;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;

COMMENT ON SCHEMA raw IS 'Dados brutos importados das fontes originais (CSV, XLSX, Google Sheets), tipagem fraca.';
COMMENT ON SCHEMA etl IS 'Controle de execução de cargas e quarentena de registros invalidos. Acesso restrito a administradores.';
COMMENT ON SCHEMA core IS 'Dados limpos, deduplicados, normalizados e relacionados (modelo operacional/analitico interno).';
COMMENT ON SCHEMA mart IS 'Modelo dimensional e views analiticas destinadas ao consumo pelo Power BI.';
