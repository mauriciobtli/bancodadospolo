"""etl.config._build_url usa sqlalchemy.engine.URL.create (não montagem
manual por f-string) — precisa funcionar com senha contendo caracteres
especiais (@, :, /, %, espaço), que quebrariam uma concatenação manual."""
from __future__ import annotations

from sqlalchemy.engine import make_url

from etl.config import DatabaseSettings, _build_url


def test_url_com_senha_de_caracteres_especiais_faz_round_trip():
    settings = DatabaseSettings(
        host="localhost",
        port="5432",
        dbname="polo_inovale",
        user="polo_admin",
        password="se@nha:com/vários%estranhos espaço",
    )
    url_str = _build_url(settings)

    parsed = make_url(url_str)
    assert parsed.username == settings.user
    assert parsed.password == settings.password
    assert parsed.host == settings.host
    assert parsed.port == int(settings.port)
    assert parsed.database == settings.dbname
    assert parsed.drivername == "postgresql+psycopg"


def test_url_simples_sem_caracteres_especiais():
    settings = DatabaseSettings(
        host="db.exemplo.com", port="5433", dbname="minha_base", user="usuario", password="senha123",
    )
    url_str = _build_url(settings)
    parsed = make_url(url_str)
    assert parsed.username == "usuario"
    assert parsed.password == "senha123"
    assert parsed.host == "db.exemplo.com"
    assert parsed.port == 5433
    assert parsed.database == "minha_base"
