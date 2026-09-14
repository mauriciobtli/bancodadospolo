from etl.transforms.datas import parse_ano, parse_data
from etl.transforms.normalizacao import (
    normalizar_booleano,
    normalizar_codigo,
    normalizar_nome_organizacao,
    normalizar_texto,
)


def test_normalizar_texto_colapsa_espacos():
    assert normalizar_texto("  Alfa   Tech  ") == "Alfa Tech"


def test_normalizar_texto_none_e_vazio():
    assert normalizar_texto(None) is None
    assert normalizar_texto("   ") is None


def test_normalizar_nome_organizacao_remove_acento_e_pontuacao():
    assert normalizar_nome_organizacao("Alfa Tecnologia Ltda.") == "alfa tecnologia ltda"
    assert normalizar_nome_organizacao("Instituição Gama") == "instituicao gama"


def test_normalizar_codigo_snake_case():
    assert normalizar_codigo("Tecnologia da Informação") == "tecnologia_da_informacao"


def test_normalizar_booleano_variacoes():
    for valor in ("sim", "S", "true", "1", "Verdadeiro"):
        assert normalizar_booleano(valor) is True
    for valor in ("nao", "não", "N", "false", "0"):
        assert normalizar_booleano(valor) is False
    assert normalizar_booleano(None) is None
    assert normalizar_booleano("talvez") is None


def test_parse_data_formatos_multiplos():
    import datetime as dt

    assert parse_data("15/03/2022") == dt.date(2022, 3, 15)
    assert parse_data("2022-03-15") == dt.date(2022, 3, 15)
    assert parse_data(None) is None
    assert parse_data("data invalida") is None


def test_parse_ano_faixa_valida():
    assert parse_ano("2022") == 2022
    assert parse_ano("1800") is None
    assert parse_ano("abc") is None
    assert parse_ano(None) is None
