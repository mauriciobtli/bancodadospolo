"""Fixtures compartilhadas dos testes do admin web.

Estrategia de banco de teste (separada da role de producao — ver
webapp/README.md, seção "Testes automatizados"): os testes rodam DIRETO
contra o mesmo Postgres de desenvolvimento/CI já provisionado (Alembic
`upgrade head` + `manage.py migrate` já aplicados), usando a role real
`django_app` (mesmo privilégio mínimo de produção) via `DATABASES` em
`config/settings.py` — nunca uma role com CREATEDB. `django_db_setup`
abaixo sobrescreve o comportamento padrão do pytest-django (que criaria e
apagaria um banco de teste via `CREATE DATABASE`/`DROP DATABASE`, exigindo
CREATEDB da role usada) para simplesmente reusar o banco já configurado.
Cada teste que toca o banco roda dentro de uma transação revertida ao
final (fixture `db`/marker `django_db` do pytest-django), então nenhum
teste deixa dado residual — o mesmo padrão já usado por `tests/conftest.py`
(a suíte do Data Warehouse) no mesmo Postgres.

Uma exceção: fixtures que gravam em `etl.*`/`raw.*` (django_app só tem
SELECT nesses schemas — ver db/roles/django_app.sql) usam uma conexão
separada (a role de administração do ETL) e fazem sua própria limpeza
manual, já que ficam fora da transação do Django.
"""
from __future__ import annotations

import pytest
from django.contrib.auth.models import Group, User


@pytest.fixture(scope="session")
def django_db_setup():
    """Não cria/apaga um banco de teste via CREATE DATABASE (exigiria
    privilégio CREATEDB da role de produção django_app, que este projeto
    deliberadamente não concede). Reusa o banco já configurado em
    DATABASES["default"], com o schema core/etl/raw (Alembic) e o schema
    app (manage.py migrate, incluindo os grupos/permissões da migration
    core_admin.0001_initial) já aplicados."""


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
