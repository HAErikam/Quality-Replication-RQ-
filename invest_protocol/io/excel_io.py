"""Lectura y escritura de archivos Excel del protocolo experimental."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from invest_protocol.constants import (
    ENTRADA_COLS,
    EVALUADA_COLS,
    MEJORADA_COLS,
    REEVALUADA_COLS,
    SHEET_ENTRADA,
    SHEET_EVALUADA,
    SHEET_MEJORADA,
    SHEET_REEVALUADA,
)


def leer_entrada_desde_excel(xlsx_path: Path) -> pd.DataFrame:
    """Lee la hoja 'Entrada' verificando columnas requeridas.

    Se toleran algunas variaciones comunes del nombre de la columna
    'Estado de tarea' para mejorar robustez sin alterar el protocolo.
    """
    if not xlsx_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name=SHEET_ENTRADA, dtype=str, engine="openpyxl")
    df = df.fillna("")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(
        columns={
            "Estado de Tarea": "Estado de tarea",
            "estado de tarea": "Estado de tarea",
            "ESTADO DE TAREA": "Estado de tarea",
        }
    )

    for col in ENTRADA_COLS:
        if col not in df.columns:
            raise ValueError(
                f"Falta la columna requerida '{col}' en hoja '{SHEET_ENTRADA}'. "
                f"Columnas encontradas: {list(df.columns)}"
            )

    return df[ENTRADA_COLS].copy()


def exportar_resultados_excel(
    out_path: Path,
    df_entrada: pd.DataFrame,
    df_evaluada: pd.DataFrame,
    df_mejorada: pd.DataFrame,
    df_reevaluada: pd.DataFrame,
) -> None:
    """Escribe un único Excel con las cuatro hojas del protocolo."""
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_entrada.to_excel(writer, sheet_name=SHEET_ENTRADA, index=False)
        df_evaluada[EVALUADA_COLS].to_excel(writer, sheet_name=SHEET_EVALUADA, index=False)
        df_mejorada[MEJORADA_COLS].to_excel(writer, sheet_name=SHEET_MEJORADA, index=False)
        df_reevaluada[REEVALUADA_COLS].to_excel(writer, sheet_name=SHEET_REEVALUADA, index=False)


def exportar_meta_json(meta_path: Path, meta: dict[str, Any]) -> None:
    """Guarda el archivo de metadatos de la corrida experimental."""
    with open(meta_path, "w", encoding="utf-8") as handle:
        json.dump(meta, handle, ensure_ascii=False, indent=2)
