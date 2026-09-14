-- Funcao utilitaria compartilhada: mantem atualizado_em em dia em qualquer UPDATE.
CREATE OR REPLACE FUNCTION core.fn_atualizado_em()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.atualizado_em := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION core.fn_atualizado_em() IS 'Trigger BEFORE UPDATE que atualiza a coluna atualizado_em para now().';
