#!/usr/bin/env python
"""Utilitario de linha de comando do Django (manage.py padrao)."""
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Nao foi possivel importar o Django. Ative o ambiente virtual e "
            "instale as dependencias (pip install -e \".[webapp]\")."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
