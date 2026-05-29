**## Cómo evaluar**

1\. Antes de comenzar, validar que sobre el repo limpio (sin tocar) las pruebas fallan:
   ```bash
   ./run_exam_tests.sh
   ```
   Salida esperada en estado roto: las suites `tests/test_inventory.py` y `tests/test_exam_fixes.py` reportan fallos; `tests/test_events.py` también muestra fallos derivados (router prefix + modelo Tier).

2\. Tras la entrega del estudiante, repetir:
   ```bash
   ./run_exam_tests.sh
   ```
   Debe salir todo verde. 


# Business Logic
Implement this business logic

Inventory / capacity enforcement. When the API returns availability for the main resource. The
computation must be correct under concurrent reads (you do not need to handle concurrent writes —
those go through admin).