"""Normalizacao e validacao de CNPJ (Cadastro Nacional da Pessoa Juridica)."""
from __future__ import annotations

import re

_NON_DIGITS = re.compile(r"\D+")
_WEIGHTS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_WEIGHTS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def normalize_cnpj(raw_value: str | None) -> str | None:
    """Remove mascara/pontuacao, retorna apenas digitos ou None se vazio."""
    if raw_value is None:
        return None
    digits = _NON_DIGITS.sub("", raw_value)
    return digits or None


def _check_digit(digits: str, weights: list[int]) -> int:
    total = sum(int(d) * w for d, w in zip(digits, weights))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def is_valid_cnpj(raw_value: str | None) -> bool:
    """Valida o CNPJ pelo algoritmo de digitos verificadores.

    Retorna False para None/vazio, tamanho diferente de 14 digitos, ou
    sequencias repetidas (00000000000000, 11111111111111, ...), que sao
    matematicamente "validas" pelo algoritmo mas nunca sao CNPJs reais.
    """
    digits = normalize_cnpj(raw_value)
    if digits is None or len(digits) != 14:
        return False
    if digits == digits[0] * 14:
        return False

    first_check = _check_digit(digits[:12], _WEIGHTS_1)
    if first_check != int(digits[12]):
        return False

    second_check = _check_digit(digits[:13], _WEIGHTS_2)
    return second_check == int(digits[13])
