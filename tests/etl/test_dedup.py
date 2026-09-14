from etl.transforms.dedup_organizacao import calcular_chave


def test_calcular_chave_usa_cnpj_quando_valido():
    chave = calcular_chave("11.122.233/0001-83", "Alfa Tecnologia", 1)
    assert chave is not None
    assert chave.tipo == "cnpj"
    assert chave.valor == "11122233000183"


def test_calcular_chave_ignora_cnpj_invalido_e_usa_nome_municipio():
    chave = calcular_chave("00.000.000/0000-00", "Instituto Gama", 5)
    assert chave is not None
    assert chave.tipo == "nome_municipio"
    assert chave.valor == "instituto gama|5"


def test_calcular_chave_sem_cnpj_usa_nome_municipio():
    chave = calcular_chave(None, "Beta Startup", None)
    assert chave is not None
    assert chave.tipo == "nome_municipio"
    assert chave.valor == "beta startup|sem_municipio"


def test_calcular_chave_sem_nome_nem_cnpj_retorna_none():
    assert calcular_chave(None, None, 1) is None
