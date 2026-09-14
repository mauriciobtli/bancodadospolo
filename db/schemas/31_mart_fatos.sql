-- =========================================================================
-- mart: fatos
-- =========================================================================

CREATE OR REPLACE VIEW mart.fato_investimento_inovacao AS
SELECT id_fato, id_organizacao, id_tempo, id_fonte_recurso, id_projeto, categoria, valor, observacao
FROM core.fato_investimento_inovacao;

-- Tecnologia "achatada": tecnologia principal (bridge.principal) resolve a
-- coluna id_tecnologia_principal sem gerar fanout no modelo do Power BI.
-- Para analises N:N explicitas, usar mart.bridge_inovacao_tecnologia.
CREATE OR REPLACE VIEW mart.fato_inovacao AS
SELECT
    fi.id_inovacao,
    fi.id_organizacao,
    fi.id_projeto,
    fi.nome,
    fi.descricao,
    fi.id_tipo_inovacao,
    fi.id_grau_novidade,
    fi.id_problema_alvo,
    tec_principal.id_tecnologia AS id_tecnologia_principal,
    t.nome AS tecnologia_principal_nome,
    (
        SELECT string_agg(dt2.nome, ', ' ORDER BY dt2.nome)
        FROM core.bridge_inovacao_tecnologia b2
        JOIN core.dim_tecnologia dt2 ON dt2.id_tecnologia = b2.id_tecnologia
        WHERE b2.id_inovacao = fi.id_inovacao
    ) AS tecnologias_relacionadas,
    fi.data_inicio,
    fi.data_implementacao,
    fi.status,
    fi.chegou_ao_mercado,
    fi.mercado_alvo,
    fi.impacto_trabalho,
    fi.receita_associada,
    fi.reducao_custo_estimada,
    fi.aumento_capacidade_percentual,
    fi.empregos_criados,
    fi.empregos_qualificados_criados
FROM core.fato_inovacao fi
LEFT JOIN core.bridge_inovacao_tecnologia tec_principal
    ON tec_principal.id_inovacao = fi.id_inovacao AND tec_principal.principal
LEFT JOIN core.dim_tecnologia t ON t.id_tecnologia = tec_principal.id_tecnologia;
COMMENT ON VIEW mart.fato_inovacao IS 'Fato inovacao achatado: tecnologia principal em coluna (sem N:N) + lista textual de tecnologias relacionadas.';

CREATE OR REPLACE VIEW mart.bridge_inovacao_tecnologia AS
SELECT id_inovacao, id_tecnologia, principal
FROM core.bridge_inovacao_tecnologia;
COMMENT ON VIEW mart.bridge_inovacao_tecnologia IS 'Relacionamento N:N explicito inovacao-tecnologia. Usar com cautela no Power BI (cria fanout); prefira mart.fato_inovacao para o caso geral.';

CREATE OR REPLACE VIEW mart.bridge_projeto_organizacao AS
SELECT
    bpo.id_projeto,
    bpo.id_organizacao,
    o.nome AS organizacao_nome,
    o.tipo_organizacao,
    bpo.papel,
    bpo.data_entrada,
    bpo.data_saida
FROM core.bridge_projeto_organizacao bpo
JOIN core.dim_organizacao o ON o.id_organizacao = bpo.id_organizacao;
COMMENT ON VIEW mart.bridge_projeto_organizacao IS 'Participantes de cada projeto e seus papeis (lider, parceiro, executor, financiador, universidade, ICT, fornecedor...). N:N — use com cautela no Power BI (fanout); mart.dim_projeto.organizacao_lider_nome cobre o caso comum de "quem lidera".';

CREATE OR REPLACE VIEW mart.bridge_projeto_tecnologia AS
SELECT
    bpt.id_projeto,
    bpt.id_tecnologia,
    t.nome AS tecnologia_nome,
    bpt.principal
FROM core.bridge_projeto_tecnologia bpt
JOIN core.dim_tecnologia t ON t.id_tecnologia = bpt.id_tecnologia;
COMMENT ON VIEW mart.bridge_projeto_tecnologia IS 'Tecnologias associadas a cada projeto (N:N). Use com cautela no Power BI (fanout); mart.dim_projeto.tecnologia_principal_nome cobre o caso comum de "tecnologia principal".';

CREATE OR REPLACE VIEW mart.fato_conexao_ecossistema AS
SELECT
    c.id_conexao,
    c.id_organizacao_origem,
    oo.nome AS organizacao_origem_nome,
    oo.tipo_organizacao AS tipo_organizacao_origem,
    c.id_organizacao_destino,
    od.nome AS organizacao_destino_nome,
    od.tipo_organizacao AS tipo_organizacao_destino,
    c.tipo_conexao,
    c.data_inicio,
    c.data_fim,
    c.id_projeto,
    c.valor_financeiro,
    c.gerou_projeto,
    c.gerou_contrato,
    c.gerou_inovacao
FROM core.fato_conexao_ecossistema c
JOIN core.dim_organizacao oo ON oo.id_organizacao = c.id_organizacao_origem
JOIN core.dim_organizacao od ON od.id_organizacao = c.id_organizacao_destino;

CREATE OR REPLACE VIEW mart.fato_adocao_tecnologica AS
SELECT id_fato, id_organizacao, id_tecnologia, id_tempo, nivel_adocao, ano_inicio_uso, area_aplicacao, observacao
FROM core.fato_adocao_tecnologica;

CREATE OR REPLACE VIEW mart.fato_desempenho_organizacao AS
SELECT id_fato, id_organizacao, id_tempo, faturamento, numero_empregados, numero_empregados_tecnologia,
       exportacoes, receita_produtos_novos, investimento_p_d, custos_reduzidos_por_inovacao
FROM core.fato_desempenho_organizacao;

CREATE OR REPLACE VIEW mart.fato_talento AS
SELECT id_fato, id_organizacao, id_tempo, pesquisadores_p_d, mestres, doutores,
       profissionais_stem, pessoas_capacitadas, novas_contratacoes_qualificadas
FROM core.fato_talento;

CREATE OR REPLACE VIEW mart.fato_propriedade_intelectual AS
SELECT id_pi, id_organizacao, id_projeto, tipo_pi, titulo, numero_registro,
       data_deposito, data_concessao, status, licenciada, receita_licenciamento
FROM core.fato_propriedade_intelectual;
