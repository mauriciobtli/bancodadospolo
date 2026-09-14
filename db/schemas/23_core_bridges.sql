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
-- Um projeto pode ter varios participantes com papeis funcionais
-- diferentes, e uma mesma organizacao pode acumular mais de um papel no
-- mesmo projeto (ex.: financiador e parceiro). "universidade"/"ict" NAO
-- sao papeis validos aqui — sao tipos de organizacao
-- (dim_organizacao.tipo_organizacao); uma universidade participa do
-- projeto com um papel funcional (ex.: 'executor', 'parceiro'), e o tipo
-- da organizacao ja fica disponivel via join com dim_organizacao (ver
-- mart.bridge_projeto_organizacao).
--
-- core.projeto.id_organizacao_lider permanece na tabela como atalho
-- denormalizado (usado pelas views ja existentes de mart.dim_projeto) e e
-- a FONTE DE VERDADE: os triggers abaixo mantem automaticamente a linha
-- papel='lider' desta bridge sincronizada com esse campo (nao apenas por
-- convencao documentada). O mesmo vale para bridge_projeto_tecnologia
-- abaixo em relacao a core.projeto.id_tecnologia_principal.
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
        'lider', 'parceiro', 'executor', 'financiador', 'fornecedor', 'beneficiario', 'outro'
    )),
    CONSTRAINT ck_bridge_projeto_org_datas CHECK (
        data_saida IS NULL OR data_entrada IS NULL OR data_saida >= data_entrada
    )
);
COMMENT ON TABLE core.bridge_projeto_organizacao IS 'Participantes de um projeto e seus papeis funcionais (N:N). Permite multiplos parceiros/executores/financiadores por projeto, e multiplos papeis para a mesma organizacao. O tipo da organizacao (universidade, ICT, empresa...) vem de dim_organizacao.tipo_organizacao, nao deste campo.';

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
COMMENT ON TABLE core.bridge_projeto_tecnologia IS 'Tecnologias associadas a um projeto (N:N). principal marca a tecnologia mais relevante; mantida em sincronia com core.projeto.id_tecnologia_principal pelos triggers abaixo.';

CREATE INDEX IF NOT EXISTS ix_bridge_projeto_tec_tecnologia ON core.bridge_projeto_tecnologia (id_tecnologia);

CREATE UNIQUE INDEX IF NOT EXISTS uq_bridge_projeto_tec_principal
    ON core.bridge_projeto_tecnologia (id_projeto)
    WHERE principal;

-- =========================================================================
-- Sincronizacao entre core.projeto (fonte de verdade para "quem lidera" e
-- "qual a tecnologia principal") e as bridges acima.
--
-- Estrategia (unidirecional, evita loop de triggers):
--   1. core.projeto muda  -> trigger de SYNC atualiza a bridge automaticamente.
--   2. bridge muda direto -> trigger de GUARDA rejeita qualquer papel='lider'
--      ou principal=true que nao corresponda ao valor atual em core.projeto
--      (INSERT/UPDATE) e rejeita apagar a linha que representa o valor
--      atual (DELETE). Para trocar o lider/tecnologia principal, a unica
--      forma valida e atualizar core.projeto — a bridge segue automaticamente.
-- Excluir o projeto inteiro (DELETE ON core.projeto) continua funcionando:
-- o ON DELETE CASCADE remove as linhas da bridge antes que exista uma
-- linha em core.projeto para o guard comparar, entao a exclusao em
-- cascata nunca e bloqueada pelo guard.
-- =========================================================================

CREATE OR REPLACE FUNCTION core.fn_projeto_sync_bridge_lider()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM core.bridge_projeto_organizacao
    WHERE id_projeto = NEW.id_projeto
      AND papel = 'lider'
      AND (NEW.id_organizacao_lider IS NULL OR id_organizacao <> NEW.id_organizacao_lider);

    IF NEW.id_organizacao_lider IS NOT NULL THEN
        INSERT INTO core.bridge_projeto_organizacao (id_projeto, id_organizacao, papel, fonte_dado)
        VALUES (NEW.id_projeto, NEW.id_organizacao_lider, 'lider', 'sync_core.projeto')
        ON CONFLICT (id_projeto, id_organizacao, papel) DO NOTHING;
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION core.fn_projeto_sync_bridge_lider() IS 'Mantem bridge_projeto_organizacao.papel=lider sincronizada com core.projeto.id_organizacao_lider (fonte de verdade).';

CREATE OR REPLACE TRIGGER trg_projeto_sync_bridge_lider
    AFTER INSERT OR UPDATE OF id_organizacao_lider ON core.projeto
    FOR EACH ROW EXECUTE FUNCTION core.fn_projeto_sync_bridge_lider();

CREATE OR REPLACE FUNCTION core.fn_projeto_sync_bridge_tecnologia_principal()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE core.bridge_projeto_tecnologia
    SET principal = false
    WHERE id_projeto = NEW.id_projeto
      AND principal
      AND (NEW.id_tecnologia_principal IS NULL OR id_tecnologia <> NEW.id_tecnologia_principal);

    IF NEW.id_tecnologia_principal IS NOT NULL THEN
        INSERT INTO core.bridge_projeto_tecnologia (id_projeto, id_tecnologia, principal)
        VALUES (NEW.id_projeto, NEW.id_tecnologia_principal, true)
        ON CONFLICT (id_projeto, id_tecnologia) DO UPDATE SET principal = true;
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION core.fn_projeto_sync_bridge_tecnologia_principal() IS 'Mantem bridge_projeto_tecnologia.principal sincronizada com core.projeto.id_tecnologia_principal (fonte de verdade).';

CREATE OR REPLACE TRIGGER trg_projeto_sync_bridge_tecnologia_principal
    AFTER INSERT OR UPDATE OF id_tecnologia_principal ON core.projeto
    FOR EACH ROW EXECUTE FUNCTION core.fn_projeto_sync_bridge_tecnologia_principal();

CREATE OR REPLACE FUNCTION core.fn_guard_bridge_projeto_lider()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_lider_atual bigint;
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.papel = 'lider' THEN
            SELECT id_organizacao_lider INTO v_lider_atual FROM core.projeto WHERE id_projeto = OLD.id_projeto;
            IF v_lider_atual = OLD.id_organizacao THEN
                RAISE EXCEPTION
                    'Nao e possivel apagar diretamente a linha papel=lider do projeto %. Para trocar ou remover o lider, atualize core.projeto.id_organizacao_lider (fonte de verdade) — a bridge e sincronizada automaticamente.',
                    OLD.id_projeto
                    USING ERRCODE = 'check_violation';
            END IF;
        END IF;
        RETURN OLD;
    END IF;

    IF NEW.papel = 'lider' THEN
        SELECT id_organizacao_lider INTO v_lider_atual FROM core.projeto WHERE id_projeto = NEW.id_projeto;
        IF v_lider_atual IS DISTINCT FROM NEW.id_organizacao THEN
            RAISE EXCEPTION
                'Nao e possivel gravar papel=lider para a organizacao % no projeto % diretamente na bridge: o lider atual (core.projeto.id_organizacao_lider) e %. Atualize core.projeto.id_organizacao_lider — a bridge e sincronizada automaticamente.',
                NEW.id_organizacao, NEW.id_projeto, v_lider_atual
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION core.fn_guard_bridge_projeto_lider() IS 'Impede que bridge_projeto_organizacao.papel=lider divirja de core.projeto.id_organizacao_lider (fonte de verdade). Nao bloqueia a cascata de DELETE do projeto, pois o guard so dispara com o projeto ainda existente.';

CREATE OR REPLACE TRIGGER trg_guard_bridge_projeto_lider
    BEFORE INSERT OR UPDATE OR DELETE ON core.bridge_projeto_organizacao
    FOR EACH ROW EXECUTE FUNCTION core.fn_guard_bridge_projeto_lider();

CREATE OR REPLACE FUNCTION core.fn_guard_bridge_projeto_tecnologia_principal()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_tecnologia_atual bigint;
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.principal THEN
            SELECT id_tecnologia_principal INTO v_tecnologia_atual FROM core.projeto WHERE id_projeto = OLD.id_projeto;
            IF v_tecnologia_atual = OLD.id_tecnologia THEN
                RAISE EXCEPTION
                    'Nao e possivel apagar diretamente a tecnologia principal (id_tecnologia=%) do projeto %. Para trocar, atualize core.projeto.id_tecnologia_principal (fonte de verdade) — a bridge e sincronizada automaticamente.',
                    OLD.id_tecnologia, OLD.id_projeto
                    USING ERRCODE = 'check_violation';
            END IF;
        END IF;
        RETURN OLD;
    END IF;

    IF NEW.principal THEN
        SELECT id_tecnologia_principal INTO v_tecnologia_atual FROM core.projeto WHERE id_projeto = NEW.id_projeto;
        IF v_tecnologia_atual IS DISTINCT FROM NEW.id_tecnologia THEN
            RAISE EXCEPTION
                'Nao e possivel marcar principal=true para a tecnologia % no projeto % diretamente na bridge: a tecnologia principal atual (core.projeto.id_tecnologia_principal) e %. Atualize core.projeto.id_tecnologia_principal — a bridge e sincronizada automaticamente.',
                NEW.id_tecnologia, NEW.id_projeto, v_tecnologia_atual
                USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION core.fn_guard_bridge_projeto_tecnologia_principal() IS 'Impede que bridge_projeto_tecnologia.principal divirja de core.projeto.id_tecnologia_principal (fonte de verdade). Nao bloqueia a cascata de DELETE do projeto, pois o guard so dispara com o projeto ainda existente.';

CREATE OR REPLACE TRIGGER trg_guard_bridge_projeto_tecnologia_principal
    BEFORE INSERT OR UPDATE OR DELETE ON core.bridge_projeto_tecnologia
    FOR EACH ROW EXECUTE FUNCTION core.fn_guard_bridge_projeto_tecnologia_principal();
