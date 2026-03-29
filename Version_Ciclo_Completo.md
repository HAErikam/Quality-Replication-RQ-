# Cambios de la versión de ciclo completo

Esta versión mantiene la lógica general del protocolo INVEST, el mismo modelo y la misma temperatura, pero cambia la estrategia de ejecución:

- **Versión original**: ejecutaba 6 veces la **Fase 1 (evaluación)** y luego corría **Fase 2 (mejora)** y **Fase 3 (reevaluación)** solo una vez, tomando una corrida base.
- **Nueva versión**: ejecuta **6 veces el ciclo completo**:
  1. evaluación,
  2. mejora,
  3. reevaluación.

## Impacto en la trazabilidad

- `ID_corrida` ahora identifica una corrida completa del ciclo.
- Las hojas `Evaluada`, `Mejorada` y `Reevaluada` quedan alineadas por `ID_corrida`.
- El parámetro `usar_corrida_base_f2_f3` se conserva solo por compatibilidad, pero ya no altera la lógica.

## Archivos ajustados

- `invest_protocol/pipeline.py`
- `invest_protocol/cli.py`
- `run_pipeline.py`
- `README.md`
