"""Script mínimo para ejecutar el paquete desde la raíz del proyecto."""

from invest_protocol.pipeline import ejecutar_pipeline_invest_excel


def mostrar_progreso(payload: dict) -> None:
    evento = payload.get("evento", "")

    if evento == "inicio_pipeline":
        print(
            f"[INFO] Iniciando pipeline | filas={payload.get('filas')} | "
            f"runs_fase1={payload.get('runs_fase1')}"
        )

    elif evento == "inicio_corrida":
        print(
            f"[INFO] Iniciando corrida completa {payload.get('run')}/{payload.get('runs_fase1')}"
        )

    elif evento == "inicio_item":
        fase = payload.get("fase")
        item_id = payload.get("id", "")
        run = payload.get("run")
        runs_fase1 = payload.get("runs_fase1")
        print(f"[INFO] Fase {fase} | ID={item_id} | corrida {run}/{runs_fase1}")

    elif evento == "fin_item":
        fase = payload.get("fase")
        item_id = payload.get("id", "")
        run = payload.get("run")
        tokens = payload.get("tokens_total", "")
        print(f"[OK] Fase {fase} completada | ID={item_id} | corrida={run} | tokens={tokens}")

    elif evento == "fin_corrida":
        print(
            f"[OK] Corrida completa finalizada {payload.get('run')}/{payload.get('runs_fase1')}"
        )

    elif evento == "fin_pipeline":
        print("[OK] Pipeline finalizado")
        print(f"[OK] Excel salida: {payload.get('excel_salida')}")
        print(f"[OK] Tokens totales: {payload.get('tokens_total')}")
        print(f"[OK] Costo USD: {payload.get('cost_usd')}")


if __name__ == "__main__":
    meta = ejecutar_pipeline_invest_excel(
        ruta_excel_entrada="historias_entrada.xlsx",
        runs_fase1=6,
        model="gpt-5.1",
        temperature=0.2,
        usar_corrida_base_f2_f3=1,
        on_progress=mostrar_progreso,
    )

    print("\n[RESULTADO META]")
    print(meta)