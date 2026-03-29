"""Construcción de prompts por fase, usando el protocolo externo."""

from __future__ import annotations

from invest_protocol.constants import (
    COL_CA,
    COL_CLASIF,
    COL_DESC,
    COL_ESTADO,
    COL_ID,
    COL_PROY,
    COL_TITULO,
)
from invest_protocol.protocols.loader import (
    ANTI_REGALO_EVAL,
    CANDADO_F2_INCIDENTE,
    cargar_protocolo,
)


def build_prompt_f1_evaluar(row: dict) -> str:
    """Construye el prompt de evaluación de Fase 1.

    La entrada debe copiarse textual, sin correcciones ni inferencias.
    """
    protocolo = cargar_protocolo()
    return f"""
{protocolo}
{ANTI_REGALO_EVAL}
FASE 1 — EVALUACIÓN (SOBRE ENTRADA)
Evalúa cada historia EXACTAMENTE como está escrita.
❌ No inventes ni completes datos.
❌ No resumir, corregir, mejorar ni reordenar los textos originales.
Si un campo está vacío, debe permanecer vacío en la salida.

ENTRADA (copiar textual):
- ID: {row.get(COL_ID, "")}
- Estado de tarea: {row.get(COL_ESTADO, "")}
- Título: {row.get(COL_TITULO, "")}
- Descripción: {row.get(COL_DESC, "")}
- Proyecto: {row.get(COL_PROY, "")}
- Criterios de aceptación: {row.get(COL_CA, "")}

SALIDA OBLIGATORIA (SOLO JSON):
{{
  "Clasificación": "✅ Historia estándar completa | ⚠ Historia incompleta | ⚠ Historia sin estructura estándar | 🔴 Incidente o reporte de error | 🔹 Historia habilitadora | ⚠ Épica disfrazada",
  "I": 1,
  "N": 1,
  "V": 1,
  "E": 1,
  "S": 1,
  "T": 1,
  "Observaciones y Comentario Experto": "Justifica clasificación + cada penalización INVEST. Si falta Como–Quiero–Para o GWT, indícalo explícitamente."
}}
""".strip()


def build_prompt_f2_mejorar(evaluada_row: dict) -> str:
    """Construye el prompt de mejora de Fase 2."""
    protocolo = cargar_protocolo()
    clasif_f1 = str(evaluada_row.get(COL_CLASIF, "")).strip()
    return f"""
{protocolo}
{CANDADO_F2_INCIDENTE}
FASE 2 — MEJORA (IR ↔ PO)
Mejora la historia evaluada en Fase 1 siguiendo estrictamente el protocolo.
❌ No inventes funcionalidades no implícitas.
Si declaras supuestos, deben ser explícitos, mínimos y NO cambiar el alcance.
Si no es posible definir criterios sin inventar: usa EXACTO: [criterios de aceptación no definidos]

ENTRADA (desde Fase 1):
- ID: {evaluada_row.get(COL_ID, "")}
- Estado de tarea: {evaluada_row.get(COL_ESTADO, "")}
- Proyecto: {evaluada_row.get(COL_PROY, "")}
- Título: {evaluada_row.get(COL_TITULO, "")}
- Descripción: {evaluada_row.get(COL_DESC, "")}
- Criterios de aceptación: {evaluada_row.get(COL_CA, "")}
- Clasificación (F1): {clasif_f1}
- Observaciones (F1): {evaluada_row.get('Observaciones y Comentario Experto', '')}

INSTRUCCIONES DE SALIDA (OBLIGATORIO):
- Devuelve SOLO JSON válido, sin texto adicional.
- Puedes retornar 1 o más items (si divides épica: mismo ID + sufijo 25a, 25b...).
- IMPORTANTE: si Clasificación(F1) es incidente, aplica el CANDADO de arriba (NO APLICA).
- Cada item debe incluir EXACTAMENTE estas claves:
  "ID", "Estado de tarea", "Proyecto", "Título",
  "Descripción (historia mejorada)", "Criterios de aceptación (mejorados)",
  "Clasificación", "Observaciones (historia original)",
  "Observaciones (historia mejorada, con interacción IR ↔ PO, mini-checklist INVEST y aporte experto)"

Formato JSON:
{{
  "items": [
    {{
      "ID": "{evaluada_row.get(COL_ID, '')}",
      "Estado de tarea": "{evaluada_row.get(COL_ESTADO, '')}",
      "Proyecto": "{evaluada_row.get(COL_PROY, '')}",
      "Título": "{evaluada_row.get(COL_TITULO, '')}",
      "Descripción (historia mejorada)": "…",
      "Criterios de aceptación (mejorados)": "…",
      "Clasificación": "✅ Historia estándar completa | ⚠ Historia incompleta | ⚠ Historia sin estructura estándar | 🔴 Incidente o reporte de error | 🔹 Historia habilitadora | ⚠ Épica disfrazada",
      "Observaciones (historia original)": "…",
      "Observaciones (historia mejorada, con interacción IR ↔ PO, mini-checklist INVEST y aporte experto)": "IR↔PO: … (breve)\\nI ✔/⚠/❌ (nota)\\nN ✔/⚠/❌ (nota)\\nV ✔/⚠/❌ (nota)\\nE ✔/⚠/❌ (nota)\\nS ✔/⚠/❌ (nota)\\nT ✔/⚠/❌ (nota)\\nAporte experto: …"
    }}
  ]
}}
""".strip()


def build_prompt_f3_reevaluar(desde_f2_row: dict) -> str:
    """Construye el prompt de re-evaluación de Fase 3."""
    protocolo = cargar_protocolo()
    return f"""
{protocolo}
{ANTI_REGALO_EVAL}
FASE 3 — RE-EVALUACIÓN (SOBRE SALIDA DE FASE 2)
Evalúa la historia mejorada tal cual está escrita en Fase 2.
❌ No inventes ni completes datos.
❌ No corrijas textos.
Debes incluir veredicto explícito: ¿Fase 2 resolvió Fase 1? (Sí/Parcial/No + por qué).

ENTRADA (copiar textual desde Fase 2):
- ID: {desde_f2_row.get(COL_ID, '')}
- Estado de tarea: {desde_f2_row.get(COL_ESTADO, '')}
- Título: {desde_f2_row.get(COL_TITULO, '')}
- Descripción (mejorada): {desde_f2_row.get('Descripción (mejorada)', '')}
- Proyecto: {desde_f2_row.get(COL_PROY, '')}
- Criterios de aceptación (mejorados): {desde_f2_row.get('Criterios de aceptación (mejorados)', '')}

SALIDA OBLIGATORIA (SOLO JSON):
{{
  "Clasificación": "✅ Historia estándar completa | ⚠ Historia incompleta | ⚠ Historia sin estructura estándar | 🔴 Incidente o reporte de error | 🔹 Historia habilitadora | ⚠ Épica disfrazada",
  "I": 1,
  "N": 1,
  "V": 1,
  "E": 1,
  "S": 1,
  "T": 1,
  "Observaciones y Comentario Experto": "Incluye explicación, penalizaciones INVEST y validación explícita: si Fase 2 resolvió Fase 1 (Sí/Parcial/No + por qué)."
}}
""".strip()
