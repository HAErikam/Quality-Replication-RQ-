"""Interfaz de línea de comandos para ejecutar el protocolo experimental."""

from __future__ import annotations

import argparse
import json

from invest_protocol.constants import (
    DEFAULT_CORRIDA_BASE_F2_F3,
    DEFAULT_MODEL,
    DEFAULT_RUNS_FASE1,
    DEFAULT_TEMPERATURE,
)
from invest_protocol.pipeline import ejecutar_pipeline_invest_excel


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser CLI con parámetros reproducibles."""
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline INVEST de 3 fases sobre un Excel con hoja 'Entrada', repitiendo el ciclo completo por corrida."
    )
    parser.add_argument("ruta_excel_entrada", help="Ruta al archivo .xlsx de entrada")
    parser.add_argument("--runs-fase1", type=int, default=DEFAULT_RUNS_FASE1)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument(
        "--corrida-base-f2-f3",
        type=int,
        default=DEFAULT_CORRIDA_BASE_F2_F3,
        dest="usar_corrida_base_f2_f3",
        help="Parámetro conservado por compatibilidad; en esta versión no altera la ejecución.",
    )
    return parser


def main() -> None:
    """Punto de entrada ejecutable desde terminal."""
    args = build_parser().parse_args()
    meta = ejecutar_pipeline_invest_excel(
        ruta_excel_entrada=args.ruta_excel_entrada,
        runs_fase1=args.runs_fase1,
        model=args.model,
        temperature=args.temperature,
        usar_corrida_base_f2_f3=args.usar_corrida_base_f2_f3,
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
