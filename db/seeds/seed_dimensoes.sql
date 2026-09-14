-- =========================================================================
-- Seed idempotente das dimensoes fixas.
-- Todas as inserções usam ON CONFLICT DO NOTHING por chave natural (codigo),
-- portanto pode ser executado multiplas vezes sem duplicar dados.
-- =========================================================================

-- ---------------------------------------------------------------- dim_tempo
-- Grao diario, de 2015-01-01 a 2035-12-31. id_tempo = AAAAMMDD.
INSERT INTO core.dim_tempo (id_tempo, data, dia, mes, nome_mes, trimestre, ano)
SELECT
    (to_char(d, 'YYYYMMDD'))::bigint,
    d,
    extract(day FROM d)::smallint,
    extract(month FROM d)::smallint,
    to_char(d, 'TMMonth'),
    extract(quarter FROM d)::smallint,
    extract(year FROM d)::smallint
FROM generate_series('2015-01-01'::date, '2035-12-31'::date, interval '1 day') AS d
ON CONFLICT (id_tempo) DO NOTHING;

-- ---------------------------------------------------------------- dim_setor
INSERT INTO core.dim_setor (codigo, nome, descricao) VALUES
    ('agroindustria',        'Agroindustria',                 NULL),
    ('industria_transformacao', 'Industria de transformacao', NULL),
    ('tecnologia_informacao', 'Tecnologia da informacao',     NULL),
    ('saude',                'Saude',                         NULL),
    ('energia',               'Energia',                      NULL),
    ('educacao',              'Educacao',                     NULL),
    ('servicos',              'Servicos',                     NULL),
    ('comercio',              'Comercio',                     NULL),
    ('construcao_civil',      'Construcao civil',             NULL),
    ('logistica_transporte',  'Logistica e transporte',       NULL),
    ('outros',                'Outros',                       NULL)
ON CONFLICT (codigo) DO NOTHING;

-- ------------------------------------------------------------ dim_tecnologia
INSERT INTO core.dim_tecnologia (codigo, nome, descricao) VALUES
    ('inteligencia_artificial', 'Inteligencia Artificial',   NULL),
    ('dados_analytics',         'Dados e Analytics',         NULL),
    ('iot',                     'Internet das Coisas (IoT)', NULL),
    ('robotica',                'Robotica',                  NULL),
    ('biotecnologia',           'Biotecnologia',             NULL),
    ('manufatura_avancada',     'Manufatura avancada',       NULL),
    ('cloud',                   'Computacao em nuvem',       NULL),
    ('ciberseguranca',          'Ciberseguranca',            NULL),
    ('energia',                 'Tecnologias de energia',    NULL),
    ('software',                'Software',                  NULL)
ON CONFLICT (codigo) DO NOTHING;

-- -------------------------------------------------------- dim_tipo_inovacao
INSERT INTO core.dim_tipo_inovacao (codigo, nome) VALUES
    ('produto',               'Produto'),
    ('servico',                'Servico'),
    ('processo_produtivo',     'Processo produtivo'),
    ('processo_negocio',       'Processo de negocio'),
    ('modelo_negocio',         'Modelo de negocio'),
    ('tecnologia_habilitadora','Tecnologia habilitadora')
ON CONFLICT (codigo) DO NOTHING;

-- -------------------------------------------------------- dim_grau_novidade
INSERT INTO core.dim_grau_novidade (codigo, nome, ordem) VALUES
    ('novo_para_empresa',          'Novo para a empresa',            1),
    ('novo_para_mercado_regional',  'Novo para o mercado regional',   2),
    ('novo_para_mercado_nacional',  'Novo para o mercado nacional',   3),
    ('novo_para_mercado_mundial',   'Novo para o mercado mundial',    4)
ON CONFLICT (codigo) DO NOTHING;

-- -------------------------------------------------------- dim_fonte_recurso
INSERT INTO core.dim_fonte_recurso (codigo, nome) VALUES
    ('recursos_proprios', 'Recursos proprios'),
    ('fapesc',             'FAPESC'),
    ('finep',              'FINEP'),
    ('cnpq',               'CNPq'),
    ('embrapii',           'EMBRAPII'),
    ('investidor',         'Investidor'),
    ('credito',            'Credito'),
    ('prefeitura',         'Prefeitura'),
    ('outros',             'Outros')
ON CONFLICT (codigo) DO NOTHING;

-- -------------------------------------------------------- dim_problema_alvo
INSERT INTO core.dim_problema_alvo (codigo, nome) VALUES
    ('produtividade',        'Produtividade'),
    ('reducao_custo',        'Reducao de custo'),
    ('escassez_mao_obra',    'Escassez de mao de obra'),
    ('qualidade',            'Qualidade'),
    ('sustentabilidade',     'Sustentabilidade'),
    ('seguranca',            'Seguranca'),
    ('novos_mercados',       'Novos mercados'),
    ('experiencia_cliente',  'Experiencia do cliente'),
    ('outros',               'Outros')
ON CONFLICT (codigo) DO NOTHING;

-- ---------------------------------------------------------------- dim_municipio
-- Area de atuacao oficial do Polo Inovale: os 12 municipios da AMMOC
-- (Associacao dos Municipios do Meio Oeste Catarinense). Codigos IBGE
-- (7 digitos) conferidos em setembro/2026 contra multiplas fontes
-- independentes (IBGE Cidades, Censo 2022, QualoCEP) — recomenda-se uma
-- confirmacao final contra a tabela oficial do IBGE
-- (https://www.ibge.gov.br/explica/codigos-dos-municipios.php) antes do
-- primeiro uso em producao.
--
-- Demais municipios (fora da AMMOC, mas que venham a se relacionar com o
-- ecossistema — ex.: sede de uma universidade parceira) podem ser
-- inseridos via ETL com pertence_area_atuacao=false; o loader de
-- organizacoes faz upsert por codigo_ibge quando o municipio ainda nao
-- existir.
INSERT INTO core.dim_municipio (codigo_ibge, nome, uf, regiao, pertence_area_atuacao, fonte_dado) VALUES
    ('4209003', 'Joacaba',         'SC', 'sul', true, 'seed_ammoc'),
    ('4206702', 'Herval d''Oeste', 'SC', 'sul', true, 'seed_ammoc'),
    ('4210035', 'Luzerna',         'SC', 'sul', true, 'seed_ammoc'),
    ('4206801', 'Ibicare',         'SC', 'sul', true, 'seed_ammoc'),
    ('4218509', 'Treze Tilias',    'SC', 'sul', true, 'seed_ammoc'),
    ('4211801', 'Ouro',            'SC', 'sul', true, 'seed_ammoc'),
    ('4203907', 'Capinzal',        'SC', 'sul', true, 'seed_ammoc'),
    ('4205209', 'Erval Velho',     'SC', 'sul', true, 'seed_ammoc'),
    ('4209201', 'Lacerdopolis',    'SC', 'sul', true, 'seed_ammoc'),
    ('4204004', 'Catanduvas',      'SC', 'sul', true, 'seed_ammoc'),
    ('4200408', 'Agua Doce',       'SC', 'sul', true, 'seed_ammoc'),
    ('4219176', 'Vargem Bonita',   'SC', 'sul', true, 'seed_ammoc')
ON CONFLICT (codigo_ibge) DO NOTHING;
