"""Utilidades pequeñas y reutilizables del paquete."""

from __future__ import annotations

from typing import Any


def likert_1a5(value: Any) -> int | str:
    """Convierte un valor a entero entre 1 y 5.

    Retorna cadena vacía cuando el valor no es válido para evitar
    contaminar la salida con datos fuera del protocolo.
    """
    try:
        ivalue = int(value)
        if 1 <= ivalue <= 5:
            return ivalue
    except Exception:
        pass
    return ""


def is_incidente(clasificacion: str) -> bool:
    """Determina si una clasificación corresponde a incidente."""
    text = (clasificacion or "").strip()
    return text.startswith("🔴") or "Incidente" in text


def safe_strip(value: Any) -> str:
    """Convierte cualquier valor a texto eliminando espacios externos."""
    return str(value if value is not None else "").strip()
