"""Orquestador principal del protocolo INVEST de 3 fases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from invest_protocol.constants import (
    COL_CA,
    COL_CLASIF,
    COL_DESC,
    COL_ESTADO,
    COL_ID,
    COL_PROY,
    COL_TITULO,
    COSTS_PER_1M,
    DEFAULT_CORRIDA_BASE_F2_F3,
    DEFAULT_MODEL,
    DEFAULT_RUNS_FASE1,
    DEFAULT_TEMPERATURE,
    EVALUADA_COLS,
    MEJORADA_COLS,
    REEVALUADA_COLS,
)
from invest_protocol.core.openai_client import LLMUsage, OpenAIJsonClient
from invest_protocol.core.prompts import (
    build_prompt_f1_evaluar,
    build_prompt_f2_mejorar,
    build_prompt_f3_reevaluar,
)
from invest_protocol.io.excel_io import (
    exportar_meta_json,
    exportar_resultados_excel,
    leer_entrada_desde_excel,
)
from invest_protocol.utils.helpers import is_incidente, likert_1a5, safe_strip

ProgressCallback = Callable[[dict[str, Any]], None] | None


@dataclass(slots=True)
class UsageAccumulator:
    """Acumula métricas globales de consumo a lo largo de la corrida."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0

    def add(self, usage: LLMUsage) -> None:
        self.prompt_tokens += int(usage.prompt_tokens)
        self.completion_tokens += int(usage.completion_tokens)
        if usage.cost_usd != "":
            self.total_cost += float(usage.cost_usd)


class InvestPipeline:
    """Ejecuta el protocolo completo en tres fases.

    Diseño metodológico de esta versión:
    - Cada corrida ejecuta el ciclo completo Fase 1 → Fase 2 → Fase 3.
    - El ciclo completo se repite N veces sobre la misma entrada.
    - Se preservan modelo y temperatura en todas las corridas.
    - El parámetro ``usar_corrida_base_f2_f3`` se conserva solo por compatibilidad,
      pero ya no gobierna la lógica del pipeline.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        runs_fase1: int = DEFAULT_RUNS_FASE1,
        usar_corrida_base_f2_f3: int = DEFAULT_CORRIDA_BASE_F2_F3,
        on_progress: ProgressCallback = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.runs_fase1 = runs_fase1
        self.usar_corrida_base_f2_f3 = usar_corrida_base_f2_f3
        self.on_progress = on_progress
        self.client = OpenAIJsonClient(model=model, temperature=temperature)
        self.usage = UsageAccumulator()

    def run(self, ruta_excel_entrada: str) -> dict[str, Any]:
        """Ejecuta el pipeline completo y exporta Excel + meta.json."""
        in_path = Path(ruta_excel_entrada).expanduser().resolve()
        df_entrada = leer_entrada_desde_excel(in_path)
        fecha_corrida_utc = datetime.now(timezone.utc).isoformat()

        self._emit({
            "evento": "inicio_pipeline",
            "filas": int(df_entrada.shape[0]),
            "runs_fase1": int(self.runs_fase1),
            "metodo": "ciclo_completo_por_corrida",
        })

        df_evaluada, df_mejorada, df_reevaluada = self._ejecutar_ciclos_completos(
            df_entrada,
            fecha_corrida_utc,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_xlsx = in_path.with_name(
            f"{in_path.stem}_INVEST_3fases_ciclo_completo_runs{self.runs_fase1}_{timestamp}.xlsx"
        )
        exportar_resultados_excel(out_xlsx, df_entrada, df_evaluada, df_mejorada, df_reevaluada)

        meta = {
            "excel_entrada": str(in_path),
            "excel_salida": str(out_xlsx),
            "fecha_corrida_utc": fecha_corrida_utc,
            "filas_entrada": int(df_entrada.shape[0]),
            "runs_ciclo_completo_por_hu": int(self.runs_fase1),
            "runs_fase1_por_hu": int(self.runs_fase1),
            "corrida_base_f2_f3": None,
            "parametro_corrida_base_recibido": int(self.usar_corrida_base_f2_f3),
            "filas_evaluada": int(df_evaluada.shape[0]),
            "filas_mejorada": int(df_mejorada.shape[0]),
            "filas_reevaluada": int(df_reevaluada.shape[0]),
            "modelo": self.model,
            "temperature": float(self.temperature),
            "tokens_prompt_total": int(self.usage.prompt_tokens),
            "tokens_completion_total": int(self.usage.completion_tokens),
            "tokens_total": int(self.usage.prompt_tokens + self.usage.completion_tokens),
            "costo_total_usd": round(float(self.usage.total_cost), 6),
            "tabla_costos_usd_por_1M_tokens": COSTS_PER_1M,
            "nota_metodologica": (
                "Cada una de las corridas ejecuta el ciclo completo: Fase 1 evalúa la hoja "
                "Entrada sin modificar texto, Fase 2 mejora la salida de esa misma corrida y "
                "Fase 3 reevalúa exclusivamente la salida de Fase 2 de esa misma corrida. "
                "No se usa una corrida base única para Fases 2 y 3. Se aplican candados "
                "anti-regalo y no-mejora de incidentes."
            ),
        }
        exportar_meta_json(out_xlsx.with_suffix(".meta.json"), meta)

        self._emit({
            "evento": "fin_pipeline",
            "excel_salida": str(out_xlsx),
            "tokens_total": int(self.usage.prompt_tokens + self.usage.completion_tokens),
            "cost_usd": round(float(self.usage.total_cost), 6),
        })
        return meta

    def _ejecutar_ciclos_completos(
        self,
        df_entrada: pd.DataFrame,
        fecha_corrida_utc: str,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Ejecuta N veces el ciclo completo F1 → F2 → F3 sobre la misma entrada."""
        evaluada_rows: list[dict[str, Any]] = []
        mejorada_rows: list[dict[str, Any]] = []
        reevaluada_rows: list[dict[str, Any]] = []

        for run_id in range(1, self.runs_fase1 + 1):
            self._emit({
                "evento": "inicio_corrida",
                "run": int(run_id),
                "runs_fase1": int(self.runs_fase1),
            })

            for _, row_series in df_entrada.iterrows():
                row = row_series.to_dict()
                evaluada = self._fase_1_item(row, run_id, fecha_corrida_utc)
                evaluada_rows.append(evaluada)

                mejoradas = self._fase_2_item(evaluada, run_id, fecha_corrida_utc)
                mejorada_rows.extend(mejoradas)

                reevaluadas = self._fase_3_items(mejoradas, run_id, fecha_corrida_utc)
                reevaluada_rows.extend(reevaluadas)

            self._emit({
                "evento": "fin_corrida",
                "run": int(run_id),
                "runs_fase1": int(self.runs_fase1),
            })

        return (
            pd.DataFrame(evaluada_rows, columns=EVALUADA_COLS),
            pd.DataFrame(mejorada_rows, columns=MEJORADA_COLS),
            pd.DataFrame(reevaluada_rows, columns=REEVALUADA_COLS),
        )

    def _fase_1_item(
        self,
        row: dict[str, Any],
        run_id: int,
        fecha_corrida_utc: str,
    ) -> dict[str, Any]:
        """Evalúa una historia en una corrida específica."""
        self._emit({
            "evento": "inicio_item",
            "fase": 1,
            "id": row.get(COL_ID, ""),
            "run": int(run_id),
            "runs_fase1": int(self.runs_fase1),
        })
        data, usage = self.client.call_json(build_prompt_f1_evaluar(row))
        self.usage.add(usage)
        self._emit({
            "evento": "fin_item",
            "fase": 1,
            "id": row.get(COL_ID, ""),
            "run": int(run_id),
            "runs_fase1": int(self.runs_fase1),
            "tokens_total": usage.total_tokens,
            "cost_usd": usage.cost_usd,
        })
        return {
            COL_ID: row.get(COL_ID, ""),
            COL_ESTADO: row.get(COL_ESTADO, ""),
            COL_TITULO: row.get(COL_TITULO, ""),
            COL_DESC: row.get(COL_DESC, ""),
            COL_PROY: row.get(COL_PROY, ""),
            COL_CA: row.get(COL_CA, ""),
            COL_CLASIF: safe_strip(data.get("Clasificación", "")),
            "I": likert_1a5(data.get("I")),
            "N": likert_1a5(data.get("N")),
            "V": likert_1a5(data.get("V")),
            "E": likert_1a5(data.get("E")),
            "S": likert_1a5(data.get("S")),
            "T": likert_1a5(data.get("T")),
            "Observaciones y Comentario Experto": safe_strip(
                data.get("Observaciones y Comentario Experto", "")
            ),
            "ID_corrida": run_id,
            "fecha_corrida_utc": fecha_corrida_utc,
            "modelo": self.model,
            "temperature": float(self.temperature),
            **usage.as_dict(),
        }

    def _fase_2_item(
        self,
        ev_row: dict[str, Any],
        run_id: int,
        fecha_corrida_utc: str,
    ) -> list[dict[str, Any]]:
        """Genera historias mejoradas a partir de la evaluación de la misma corrida."""
        clasif_f1 = safe_strip(ev_row.get(COL_CLASIF, ""))
        self._emit({
            "evento": "inicio_item",
            "fase": 2,
            "id": ev_row.get(COL_ID, ""),
            "run": int(run_id),
            "runs_fase1": int(self.runs_fase1),
        })
        data, usage = self.client.call_json(build_prompt_f2_mejorar(ev_row))
        self.usage.add(usage)
        items = data.get("items", [])
        enforced_items = self._normalizar_items_fase_2(items, ev_row, clasif_f1)

        self._emit({
            "evento": "fin_item",
            "fase": 2,
            "id": ev_row.get(COL_ID, ""),
            "run": int(run_id),
            "runs_fase1": int(self.runs_fase1),
            "items_generados": len(enforced_items),
            "tokens_total": usage.total_tokens,
            "cost_usd": usage.cost_usd,
        })

        return [
            {
                COL_ID: safe_strip(item.get("ID", "")),
                COL_ESTADO: safe_strip(item.get("Estado de tarea", ev_row.get(COL_ESTADO, ""))),
                COL_PROY: safe_strip(item.get("Proyecto", ev_row.get(COL_PROY, ""))),
                COL_TITULO: safe_strip(item.get("Título", ev_row.get(COL_TITULO, ""))),
                "Descripción (historia mejorada)": safe_strip(
                    item.get("Descripción (historia mejorada)", "")
                ),
                "Criterios de aceptación (mejorados)": safe_strip(
                    item.get("Criterios de aceptación (mejorados)", "")
                ),
                COL_CLASIF: safe_strip(item.get("Clasificación", ev_row.get(COL_CLASIF, ""))),
                "Observaciones (historia original)": safe_strip(
                    item.get(
                        "Observaciones (historia original)",
                        ev_row.get("Observaciones y Comentario Experto", ""),
                    )
                ),
                "Observaciones (historia mejorada, con interacción IR ↔ PO, mini-checklist INVEST y aporte experto)": safe_strip(
                    item.get(
                        "Observaciones (historia mejorada, con interacción IR ↔ PO, mini-checklist INVEST y aporte experto)",
                        "",
                    )
                ),
                "ID_corrida": run_id,
                "fecha_corrida_utc": fecha_corrida_utc,
                "modelo": self.model,
                "temperature": float(self.temperature),
                **usage.as_dict(),
            }
            for item in enforced_items
        ]

    def _fase_3_items(
        self,
        mejoradas: list[dict[str, Any]],
        run_id: int,
        fecha_corrida_utc: str,
    ) -> list[dict[str, Any]]:
        """Re-evalúa las historias mejoradas producidas en la misma corrida."""
        reevaluadas: list[dict[str, Any]] = []

        for mj_row in mejoradas:
            self._emit({
                "evento": "inicio_item",
                "fase": 3,
                "id": mj_row.get(COL_ID, ""),
                "run": int(run_id),
                "runs_fase1": int(self.runs_fase1),
            })
            prompt_input = {
                COL_ID: mj_row.get(COL_ID, ""),
                COL_ESTADO: mj_row.get(COL_ESTADO, ""),
                COL_TITULO: mj_row.get(COL_TITULO, ""),
                "Descripción (mejorada)": mj_row.get("Descripción (historia mejorada)", ""),
                COL_PROY: mj_row.get(COL_PROY, ""),
                "Criterios de aceptación (mejorados)": mj_row.get(
                    "Criterios de aceptación (mejorados)",
                    "",
                ),
            }
            data, usage = self.client.call_json(build_prompt_f3_reevaluar(prompt_input))
            self.usage.add(usage)
            self._emit({
                "evento": "fin_item",
                "fase": 3,
                "id": mj_row.get(COL_ID, ""),
                "run": int(run_id),
                "runs_fase1": int(self.runs_fase1),
                "tokens_total": usage.total_tokens,
                "cost_usd": usage.cost_usd,
            })
            reevaluadas.append({
                COL_ID: mj_row.get(COL_ID, ""),
                COL_ESTADO: mj_row.get(COL_ESTADO, ""),
                COL_TITULO: mj_row.get(COL_TITULO, ""),
                "Descripción (mejorada)": mj_row.get("Descripción (historia mejorada)", ""),
                COL_PROY: mj_row.get(COL_PROY, ""),
                "Criterios de aceptación (mejorados)": mj_row.get(
                    "Criterios de aceptación (mejorados)",
                    "",
                ),
                COL_CLASIF: safe_strip(data.get("Clasificación", mj_row.get(COL_CLASIF, ""))),
                "I": likert_1a5(data.get("I")),
                "N": likert_1a5(data.get("N")),
                "V": likert_1a5(data.get("V")),
                "E": likert_1a5(data.get("E")),
                "S": likert_1a5(data.get("S")),
                "T": likert_1a5(data.get("T")),
                "Observaciones y Comentario Experto": safe_strip(
                    data.get("Observaciones y Comentario Experto", "")
                ),
                "ID_corrida": run_id,
                "fecha_corrida_utc": fecha_corrida_utc,
                "modelo": self.model,
                "temperature": float(self.temperature),
                **usage.as_dict(),
            })

        return reevaluadas

    def _normalizar_items_fase_2(
        self,
        items: Any,
        ev_row: dict[str, Any],
        clasif_f1: str,
    ) -> list[dict[str, Any]]:
        """Aplica fallback seguro y candados metodológicos de Fase 2."""
        if not isinstance(items, list) or not items:
            if is_incidente(clasif_f1):
                return [self._item_incidente(ev_row)]
            return [
                {
                    "ID": ev_row.get(COL_ID, ""),
                    "Estado de tarea": ev_row.get(COL_ESTADO, ""),
                    "Proyecto": ev_row.get(COL_PROY, ""),
                    "Título": ev_row.get(COL_TITULO, ""),
                    "Descripción (historia mejorada)": ev_row.get(COL_DESC, ""),
                    "Criterios de aceptación (mejorados)": "[criterios de aceptación no definidos]",
                    "Clasificación": ev_row.get(COL_CLASIF, ""),
                    "Observaciones (historia original)": ev_row.get(
                        "Observaciones y Comentario Experto", ""
                    ),
                    "Observaciones (historia mejorada, con interacción IR ↔ PO, mini-checklist INVEST y aporte experto)": (
                        "No se recibió 'items' válido; se conserva el texto original y se marca que los criterios no quedaron definidos."
                    ),
                }
            ]

        if is_incidente(clasif_f1):
            return [self._item_incidente(ev_row)]

        return items

    @staticmethod
    def _item_incidente(ev_row: dict[str, Any]) -> dict[str, Any]:
        """Construye la salida forzada para incidentes en Fase 2."""
        return {
            "ID": ev_row.get(COL_ID, ""),
            "Estado de tarea": ev_row.get(COL_ESTADO, ""),
            "Proyecto": ev_row.get(COL_PROY, ""),
            "Título": ev_row.get(COL_TITULO, ""),
            "Descripción (historia mejorada)": "[NO APLICA - ES INCIDENTE]",
            "Criterios de aceptación (mejorados)": "[NO APLICA - ES INCIDENTE]",
            "Clasificación": "🔴 Incidente o reporte de error",
            "Observaciones (historia original)": ev_row.get(
                "Observaciones y Comentario Experto", ""
            ),
            "Observaciones (historia mejorada, con interacción IR ↔ PO, mini-checklist INVEST y aporte experto)": (
                "IR↔PO: Se confirma que el registro corresponde a un incidente y no debe transformarse en historia de usuario.\n"
                "I ❌ (incidente)\nN ❌ (incidente)\nV ❌ (incidente)\n"
                "E ❌ (incidente)\nS ❌ (incidente)\nT ❌ (incidente)\n"
                "Aporte experto: Gestionar como bug o incidente dentro del flujo de soporte o pruebas."
            ),
        }

    def _emit(self, payload: dict[str, Any]) -> None:
        """Emite eventos de progreso sin romper el pipeline por errores de UI."""
        try:
            if callable(self.on_progress):
                self.on_progress(payload)
        except Exception:
            pass


def ejecutar_pipeline_invest_excel(
    ruta_excel_entrada: str,
    runs_fase1: int = DEFAULT_RUNS_FASE1,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    usar_corrida_base_f2_f3: int = DEFAULT_CORRIDA_BASE_F2_F3,
    on_progress: ProgressCallback = None,
) -> dict[str, Any]:
    """Función pública y simple para consumir el pipeline desde otros módulos."""
    pipeline = InvestPipeline(
        model=model,
        temperature=temperature,
        runs_fase1=runs_fase1,
        usar_corrida_base_f2_f3=usar_corrida_base_f2_f3,
        on_progress=on_progress,
    )
    return pipeline.run(ruta_excel_entrada)


def ejecutar_desde_gui(
    ruta_excel_limpio: str,
    runs_fase1: int = DEFAULT_RUNS_FASE1,
    usar_corrida_base_f2_f3: int = DEFAULT_CORRIDA_BASE_F2_F3,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    on_progress: ProgressCallback = None,
) -> dict[str, Any]:
    """Wrapper amigable para GUIs o integraciones externas."""
    return ejecutar_pipeline_invest_excel(
        ruta_excel_entrada=ruta_excel_limpio,
        runs_fase1=runs_fase1,
        model=model,
        temperature=temperature,
        usar_corrida_base_f2_f3=usar_corrida_base_f2_f3,
        on_progress=on_progress,
    )
