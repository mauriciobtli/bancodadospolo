"""Fixtures compartilhadas dos testes do admin web.

Estratégia de banco de teste (separada da role de produção E do banco de
produção — ver webapp/README.md, seção "Testes automatizados"): os testes
rodam contra um banco de teste SEPARADO e já provisionado (mesmas
migrations do banco de desenvolvimento/produção), apontado por
DJANGO_TEST_DB_NAME e selecionado via `config.settings_test` (ver
webapp/pytest.ini e webapp/config/settings_test.py) — nunca uma role com
CREATEDB (`django_db_setup` abaixo não deixa o pytest-django criar/apagar
banco via CREATE DATABASE/DROP DATABASE, o que exigiria esse privilégio).
Cada teste que toca o banco roda dentro de uma transação revertida ao
final (fixture `db`/marker `django_db` do pytest-django), então nenhum
teste deixa dado residual — o mesmo padrão já usado por `tests/conftest.py`
(a suíte do Data Warehouse).

Uma exceção: fixtures que gravam em `etl.*`/`raw.*` (django_app só tem
SELECT nesses schemas — ver db/roles/django_app.sql) usam uma conexão
separada (a role de administração do ETL, fixture `admin_engine` abaixo)
e fazem sua própria limpeza manual, já que ficam fora da transação do
Django. `admin_engine` aponta explicitamente para DJANGO_TEST_DB_NAME —
`etl.db.get_engine()` sozinho iria para POLO_DB_NAME (o banco de
produção/desenvolvimento), que é o banco ERRADO aqui.

Guarda contra rodar por engano no banco de produção: `settings_test.py`
já recusa subir se DJANGO_TEST_DB_NAME == POLO_DB_NAME (checagem feita
com os valores originais, antes de settings_test.py sobrescrever a
própria variável de ambiente POLO_DB_NAME para apontar `etl.config`
também para o banco de teste — ver o comentário lá). `django_db_setup`
abaixo repete a checagem em tempo de execução, mas contra um sinal mais
simples e robusto: o settings module efetivamente carregado precisa ser
`config.settings_test` (`IS_TEST_SETTINGS = True`) — não confia em
nenhum settings module específico ter sido usado por quem invocou o
pytest.
"""
from __future__ import annotations

import pytest
from django.contrib.auth.models import Group, User


@pytest.fixture(scope="session")
def django_db_setup():
    """Não cria/apaga um banco de teste via CREATE DATABASE (exigiria
    privilégio CREATEDB, que nenhuma role de produção deste projeto tem).
    Reusa o banco de teste já configurado em DATABASES["default"] (o
    schema core/etl/raw via Alembic e o schema app via manage.py migrate,
    incluindo os grupos/permissões das migrations de core_admin, já
    aplicados nele) — nunca o banco de produção/desenvolvimento."""
    from django.conf import settings

    if not getattr(settings, "IS_TEST_SETTINGS", False):
        pytest.exit(
            "RECUSANDO rodar os testes: o settings module ativo não é "
            "config.settings_test (IS_TEST_SETTINGS não está True). Rode os "
            "testes com DJANGO_SETTINGS_MODULE=config.settings_test (já é o "
            "padrão em webapp/pytest.ini) — ver webapp/README.md, seção "
            "'Testes automatizados'.",
            returncode=1,
        )


@pytest.fixture(scope="session")
def admin_engine():
    """Engine SQLAlchemy com a role de administração do ETL (POLO_DB_USER),
    usado só por fixtures que precisam gravar em etl.*/raw.* fora da
    transação do Django (django_app não tem INSERT nesses schemas).
    `config.settings_test` já sobrescreve a variável de ambiente
    POLO_DB_NAME para o banco de teste, então `etl.db.get_engine()`
    (que lê POLO_DB_NAME direto do ambiente) já aponta para o lugar
    certo aqui — nada de especial a fazer além de importar."""
    from etl.db import get_engine

    return get_engine()


@pytest.fixture
def grupo(db):
    def _grupo(nome: str) -> Group:
        return Group.objects.get(name=nome)

    return _grupo


@pytest.fixture
def cria_usuario(db, grupo):
    """Cria um usuário de teste (staff, senha fixa) e o associa aos grupos
    nomeados. `superuser=True` ignora os grupos e cria um superusuário."""

    contador = {"n": 0}

    def _cria(*grupos: str, superuser: bool = False) -> User:
        contador["n"] += 1
        username = f"teste_{contador['n']}_{'_'.join(grupos) or ('super' if superuser else 'sem_grupo')}"
        if superuser:
            usuario = User.objects.create_superuser(username, password="SenhaForte#123")  # noqa: S106
        else:
            usuario = User.objects.create_user(username, password="SenhaForte#123", is_staff=True)  # noqa: S106
            for nome_grupo in grupos:
                usuario.groups.add(grupo(nome_grupo))
        return usuario

    return _cria
