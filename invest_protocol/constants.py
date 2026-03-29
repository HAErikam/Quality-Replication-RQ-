"""Constantes de dominio, nombres de hojas y encabezados del protocolo."""

from __future__ import annotations

DEFAULT_MODEL = "gpt-5.1"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_RUNS_FASE1 = 6
DEFAULT_CORRIDA_BASE_F2_F3 = 1

# Columnas estándar de entrada
COL_ID = "ID"
COL_ESTADO = "Estado de tarea"
COL_TITULO = "Título"
COL_DESC = "Descripción"
COL_PROY = "Proyecto"
COL_CA = "Criterios de aceptación"
COL_CLASIF = "Clasificación"

# Hojas de Excel
SHEET_ENTRADA = "Entrada"
SHEET_EVALUADA = "Evaluada"
SHEET_MEJORADA = "Mejorada"
SHEET_REEVALUADA = "Reevaluada"

# Encabezados obligatorios por hoja
ENTRADA_COLS = [COL_ID, COL_ESTADO, COL_TITULO, COL_DESC, COL_PROY, COL_CA]

EVALUADA_COLS_BASE = [
    COL_ID,
    COL_ESTADO,
    COL_TITULO,
    COL_DESC,
    COL_PROY,
    COL_CA,
    COL_CLASIF,
    "I",
    "N",
    "V",
    "E",
    "S",
    "T",
    "Observaciones y Comentario Experto",
]

MEJORADA_COLS_BASE = [
    COL_ID,
    COL_ESTADO,
    COL_PROY,
    COL_TITULO,
    "Descripción (historia mejorada)",
    "Criterios de aceptación (mejorados)",
    COL_CLASIF,
    "Observaciones (historia original)",
    "Observaciones (historia mejorada, con interacción IR ↔ PO, mini-checklist INVEST y aporte experto)",
]

REEVALUADA_COLS_BASE = [
    COL_ID,
    COL_ESTADO,
    COL_TITULO,
    "Descripción (mejorada)",
    COL_PROY,
    "Criterios de aceptación (mejorados)",
    COL_CLASIF,
    "I",
    "N",
    "V",
    "E",
    "S",
    "T",
    "Observaciones y Comentario Experto",
]

TRACE_COLS = ["ID_corrida", "fecha_corrida_utc", "modelo", "temperature"]
USAGE_COLS = ["prompt_tokens", "completion_tokens", "total_tokens", "cost_usd"]

EVALUADA_COLS = EVALUADA_COLS_BASE + TRACE_COLS + USAGE_COLS
MEJORADA_COLS = MEJORADA_COLS_BASE + TRACE_COLS + USAGE_COLS
REEVALUADA_COLS = REEVALUADA_COLS_BASE + TRACE_COLS + USAGE_COLS

# Costos estimados por millón de tokens
COSTS_PER_1M = {
    "gpt-5.1": {"in": 1.25, "out": 10.00},
    "gpt-5-mini": {"in": 0.25, "out": 2.00},
    "gpt-5-nano": {"in": 0.05, "out": 0.40},
    "gpt-4.1": {"in": 3.00, "out": 12.00},
    "gpt-4.1-mini": {"in": 0.80, "out": 3.20},
    "gpt-4.1-nano": {"in": 0.20, "out": 0.80},
    "o3": {"in": 1.00, "out": 4.00},
    "o4-mini": {"in": 0.40, "out": 1.60},
    "gpt-4o": {"in": 2.50, "out": 10.00},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
}
