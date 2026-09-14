"""Normalizacao de texto/booleanos vindos de planilhas (fontes heterogeneas)."""
from __future__ import annotations

import re
import unicodedata

_ESPACOS = re.compile(r"\s+")

_VALORES_VERDADEIROS = {"sim", "s", "yes", "y", "true", "1", "verdadeiro"}
_VALORES_FALSOS = {"nao", "não", "n", "no", "false", "0", "falso"}


def normalizar_texto(valor: str | None) -> str | None:
    """Remove espacos duplicados e nas pontas. None/"" vira None."""
    if valor is None:
        return None
    texto = _ESPACOS.sub(" ", valor).strip()
    return texto or None


def normalizar_nome_organizacao(valor: str | None) -> str | None:
    """Normaliza nome de organizacao para comparacao (dedup), nao para exibicao:
    minusculas, sem acento, sem pontuacao, espacos colapsados."""
    texto = normalizar_texto(valor)
    if texto is None:
        return None
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    sem_pontuacao = re.sub(r"[^a-zA-Z0-9\s]", "", sem_acento)
    return _ESPACOS.sub(" ", sem_pontuacao).strip().lower() or None


def normalizar_codigo(valor: str | None) -> str | None:
    """snake_case sem acento, para transformar texto livre em codigo de dominio."""
    texto = normalizar_nome_organizacao(valor)
    if texto is None:
        return None
    return texto.replace(" ", "_")


def normalizar_booleano(valor: str | None) -> bool | None:
    if valor is None:
        return None
    texto = normalizar_texto(valor)
    if texto is None:
        return None
    texto_lower = texto.lower()
    if texto_lower in _VALORES_VERDADEIROS:
        return True
    if texto_lower in _VALORES_FALSOS:
        return False
    return None
