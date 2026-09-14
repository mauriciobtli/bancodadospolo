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

-- ----------------------------------------------------------------------
-- bridge_projeto_organizacao
-- Um projeto pode ter varios participantes com papeis diferentes (lider,
-- parceiro, executor, financiador, universidade, ict, fornecedor...), e
-- uma mesma organizacao pode acumular mais de um papel no mesmo projeto
-- (ex.: financiador e parceiro).
--
-- core.projeto.id_organizacao_lider permanece na tabela como atalho
-- denormalizado (usado pelas views ja existentes de mart.dim_projeto);
-- quando a bridge estiver populada, a linha com papel='lider' deve
-- corresponder ao mesmo id_organizacao de core.projeto.id_organizacao_lider.
-- O mesmo vale para bridge_projeto_tecnologia abaixo em relacao a
-- core.projeto.id_tecnologia_principal.
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.bridge_projeto_organizacao (
    id_projeto      bigint NOT NULL REFERENCES core.projeto (id_projeto) ON DELETE CASCADE,
    id_organizacao  bigint NOT NULL REFERENCES core.dim_organizacao (id_organizacao),
    papel           text NOT NULL,
    data_entrada    date,
    data_saida      date,
    fonte_dado      text NOT NULL,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id_projeto, id_organizacao, papel),
    CONSTRAINT ck_bridge_projeto_org_papel CHECK (papel IN (
        'lider', 'parceiro', 'executor', 'financiador', 'universidade', 'ict', 'fornecedor', 'outro'
    )),
    CONSTRAINT ck_bridge_projeto_org_datas CHECK (
        data_saida IS NULL OR data_entrada IS NULL OR data_saida >= data_entrada
    )
);
COMMENT ON TABLE core.bridge_projeto_organizacao IS 'Participantes de um projeto e seus papeis (N:N). Permite multiplos parceiros/executores/financiadores por projeto, e multiplos papeis para a mesma organizacao.';

CREATE INDEX IF NOT EXISTS ix_bridge_projeto_org_organizacao ON core.bridge_projeto_organizacao (id_organizacao);
CREATE INDEX IF NOT EXISTS ix_bridge_projeto_org_papel ON core.bridge_projeto_organizacao (papel);

-- ----------------------------------------------------------------------
-- bridge_projeto_tecnologia
-- Um projeto pode usar/desenvolver varias tecnologias habilitadoras.
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.bridge_projeto_tecnologia (
    id_projeto      bigint NOT NULL REFERENCES core.projeto (id_projeto) ON DELETE CASCADE,
    id_tecnologia   bigint NOT NULL REFERENCES core.dim_tecnologia (id_tecnologia),
    principal       boolean NOT NULL DEFAULT false,
    criado_em       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id_projeto, id_tecnologia)
);
COMMENT ON TABLE core.bridge_projeto_tecnologia IS 'Tecnologias associadas a um projeto (N:N). principal marca a tecnologia mais relevante (deve corresponder a core.projeto.id_tecnologia_principal quando preenchida).';

CREATE INDEX IF NOT EXISTS ix_bridge_projeto_tec_tecnologia ON core.bridge_projeto_tecnologia (id_tecnologia);

CREATE UNIQUE INDEX IF NOT EXISTS uq_bridge_projeto_tec_principal
    ON core.bridge_projeto_tecnologia (id_projeto)
    WHERE principal;
