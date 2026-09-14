-- =========================================================================
-- core: tabelas ponte (relacionamentos N:N)
-- =========================================================================

-- Uma inovacao pode envolver varias tecnologias habilitadoras.
CREATE TABLE IF NOT EXISTS core.bridge_inovacao_tecnologia (
    id_inovacao     bigint NOT NULL REFERENCES core.fato_inovacao (id_inovacao) ON DELETE CASCADE,
    id_tecnologia   bigint NOT NULL REFERENCES core.dim_tecnologia (id_tecnologia),
    principal       boolean NOT NULL DEFAULT false,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id_inovacao, id_tecnologia)
);
COMMENT ON TABLE core.bridge_inovacao_tecnologia IS 'Ponte N:N entre inovacao e tecnologias habilitadoras. principal marca a tecnologia mais relevante da inovacao (usada para achatar em mart).';

CREATE INDEX IF NOT EXISTS ix_bridge_inov_tec_tecnologia ON core.bridge_inovacao_tecnologia (id_tecnologia);

-- Garante no maximo uma tecnologia "principal" por inovacao.
CREATE UNIQUE INDEX IF NOT EXISTS uq_bridge_inov_tec_principal
    ON core.bridge_inovacao_tecnologia (id_inovacao)
    WHERE principal;
