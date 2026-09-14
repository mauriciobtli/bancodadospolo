from etl.validators.cnpj import is_valid_cnpj, normalize_cnpj

CNPJS_VALIDOS = [
    "11.122.233/0001-83",
    "22.233.344/0001-83",
    "33.344.455/0001-83",
]


def test_normalize_cnpj_remove_mascara():
    assert normalize_cnpj("11.122.233/0001-83") == "11122233000183"


def test_normalize_cnpj_none():
    assert normalize_cnpj(None) is None


def test_normalize_cnpj_vazio():
    assert normalize_cnpj("   ") is None


def test_is_valid_cnpj_aceita_cnpjs_validos():
    for cnpj in CNPJS_VALIDOS:
        assert is_valid_cnpj(cnpj), f"esperava {cnpj} valido"


def test_is_valid_cnpj_rejeita_digito_verificador_errado():
    assert not is_valid_cnpj("11.122.233/0001-84")


def test_is_valid_cnpj_rejeita_sequencia_repetida():
    assert not is_valid_cnpj("00.000.000/0000-00")
    assert not is_valid_cnpj("11.111.111/1111-11")


def test_is_valid_cnpj_rejeita_tamanho_errado():
    assert not is_valid_cnpj("123")


def test_is_valid_cnpj_rejeita_none():
    assert not is_valid_cnpj(None)
