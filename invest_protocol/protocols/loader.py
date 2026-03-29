"""Carga el protocolo completo y los bloques de refuerzo desde archivos externos."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROTOCOLO_PATH = BASE_DIR / "protocolo_invest_completo.txt"

ANTI_REGALO_EVAL = """
REGLAS DURAS (ANTI-REGALO) — OBLIGATORIAS
1) NO puedes clasificar como “✅ Historia estándar completa” si el texto NO cumple Como–Quiero–Para y/o NO tiene GWT adecuado.
2) Si NO hay GWT: T = 1 obligatorio.
3) Si es 🔴 Incidente o reporte de error: I=N=V=E=S=T = 1 obligatorios.
4) Para asignar 5 en cualquier criterio, debe existir evidencia textual clara; si falta algún componente clave, NO se permite 5.
5) Observaciones deben justificar la clasificación y CADA penalización con referencia explícita a INVEST.
""".strip()

CANDADO_F2_INCIDENTE = """
REGLAS DURAS PARA FASE 2 (INCIDENTE) — OBLIGATORIAS
Si la “Clasificación (F1)” es “🔴 Incidente o reporte de error”:
- NO convertir en historia de usuario.
- Retorna exactamente 1 item.
- "Descripción (historia mejorada)" = "[NO APLICA - ES INCIDENTE]"
- "Criterios de aceptación (mejorados)" = "[NO APLICA - ES INCIDENTE]"
- "Clasificación" = "🔴 Incidente o reporte de error"
- En Observaciones (historia mejorada) debes recomendar gestionarlo como incidente.
""".strip()


def cargar_protocolo() -> str:
    """Lee el protocolo completo desde un archivo de texto externo.

    Esto permite que el protocolo sea reutilizable desde otros scripts,
    pruebas o interfaces, y facilita su versionamiento dentro del repositorio.
    """
    return PROTOCOLO_PATH.read_text(encoding="utf-8").strip()
