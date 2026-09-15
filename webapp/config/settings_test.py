"""Settings usadas SOMENTE pela suíte de testes automatizados
(pytest-django, ver webapp/pytest.ini) — nunca pelo processo web real:
não é referenciada por manage.py/wsgi.py nem por nenhum outro settings
de produção.

Aponta `DATABASES["default"]["NAME"]` para um banco de teste SEPARADO e
já provisionado (mesmas migrations do banco de desenvolvimento/produção
— ver webapp/README.md, seção "Testes automatizados"), configurado pela
variável de ambiente DJANGO_TEST_DB_NAME. Recusa-se a subir (levanta
RuntimeError na importação, antes de qualquer teste rodar) se
DJANGO_TEST_DB_NAME não estiver definida ou for igual a POLO_DB_NAME —
os testes gravam e apagam dados livremente e NUNCA podem apontar para o
banco de produção, nem por engano.

Também sobrescreve a variável de ambiente POLO_DB_NAME em si (não só
DATABASES): `etl.config` (usado por `etl.db.get_engine()` e
`get_web_import_engine()` — inclusive dentro da view real de importação,
exercitada pelos testes via requisição HTTP) lê POLO_DB_NAME direto do
ambiente, sem passar pelo `DATABASES` do Django. Sem isso, os testes que
tocam esse caminho (fixtures que gravam em etl/raw, e o upload real via
`importacao/views.py`) iriam silenciosamente para o banco de
produção/desenvolvimento, mesmo com DATABASES apontando para o banco de
teste.
"""
from __future__ import annotations

import os

from config.settings import *  # noqa: F401,F403
from config.settings import DATABASES, _env

# A suite de testes precisa da credencial administrativa (POLO_DB_USER)
# para gravar fixtures diretamente em etl/raw (django_app só tem SELECT
# nesses schemas) — ver o aviso em config/settings.py.
IS_TEST_SETTINGS = True

_NOME_BANCO_PRODUCAO = _env("POLO_DB_NAME", obrigatorio=True)
_NOME_BANCO_TESTE = _env("DJANGO_TEST_DB_NAME", obrigatorio=True)

if _NOME_BANCO_TESTE == _NOME_BANCO_PRODUCAO:
    raise RuntimeError(
        "DJANGO_TEST_DB_NAME nao pode ser igual a POLO_DB_NAME "
        f"(ambos estao configurados como {_NOME_BANCO_PRODUCAO!r}). Os testes "
        "gravam e apagam dados livremente e NUNCA podem apontar para o banco "
        "de producao/desenvolvimento. Crie um banco de teste separado e "
        "configure DJANGO_TEST_DB_NAME com um nome diferente (ver "
        "webapp/README.md, secao 'Testes automatizados')."
    )

DATABASES["default"]["NAME"] = _NOME_BANCO_TESTE
os.environ["POLO_DB_NAME"] = _NOME_BANCO_TESTE
