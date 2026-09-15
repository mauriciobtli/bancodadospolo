"""Guarda contra os testes automatizados rodarem por engano contra o
banco de produção (item 5 da revisão pré-produção): config.settings_test
recusa subir se DJANGO_TEST_DB_NAME estiver ausente/vazia ou igual a
POLO_DB_NAME. Roda em subprocessos limpos (sem tocar o banco) para testar
o arquivo de verdade, não uma reimplementação da lógica aqui.

Usa string vazia (não a mera ausência da chave) para simular "não
definida": settings.py/settings_test.py também carregam o mesmo .env da
raiz via load_dotenv(override=False), que reintroduziria o valor real do
arquivo se a chave fosse só removida do ambiente do subprocesso."""
from __future__ import annotations

import os
import subprocess
import sys

_SCRIPT = (
    "import django, os; "
    "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test'); "
    "django.setup(); "
    "print('OK')"
)


def _rodar(env_extra: dict[str, str]) -> subprocess.CompletedProcess:
    ambiente = os.environ.copy()
    ambiente.update(env_extra)
    webapp_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=webapp_dir,
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_recusa_subir_com_test_db_igual_a_producao():
    resultado = _rodar({"DJANGO_TEST_DB_NAME": os.environ["POLO_DB_NAME"]})
    assert resultado.returncode != 0
    assert "nao pode ser igual a POLO_DB_NAME" in resultado.stderr


def test_recusa_subir_sem_test_db_name():
    resultado = _rodar({"DJANGO_TEST_DB_NAME": ""})
    assert resultado.returncode != 0
    assert "obrigatoria 'DJANGO_TEST_DB_NAME'" in resultado.stderr


def test_sobe_normalmente_com_test_db_separado():
    resultado = _rodar({"DJANGO_TEST_DB_NAME": "um_banco_de_teste_bem_diferente"})
    assert resultado.returncode == 0, resultado.stderr
    assert "OK" in resultado.stdout
