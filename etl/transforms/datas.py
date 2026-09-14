"""Parsing tolerante de datas vindas de CSV/XLSX (formatos brasileiros e ISO)."""
from __future__ import annotations

import datetime as dt

_FORMATOS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d/%m/%y",
)


def parse_data(valor: str | dt.date | dt.datetime | None) -> dt.date | None:
    """Converte texto em date. Retorna None quando vazio ou nao reconhecido
    (caller decide se isso e motivo de quarentena)."""
    if valor is None:
        return None
    if isinstance(valor, dt.datetime):
        return valor.date()
    if isinstance(valor, dt.date):
        return valor

    texto = str(valor).strip()
    if not texto:
        return None

    for formato in _FORMATOS:
        try:
            return dt.datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def parse_ano(valor: str | int | None) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        ano = int(float(str(valor).strip()))
    except ValueError:
        return None
    if ano < 1900 or ano > 2100:
        return None
    return ano
