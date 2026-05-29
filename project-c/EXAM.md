**# Examen de Recuperación – Backend**

Cómo verificar globalmente**

```bash
bash scripts/run_tests.sh
```

Crea `.venv-tests`, instala dependencias y corre todos los tests. Cuando los 4 archivos
de pruebas estén en verde, el estudiante aprobó la parte automatizable.


# Business Logic
Implement this business logic

Inventory / capacity enforcement. When the API returns availability for the main resource. The
computation must be correct under concurrent reads (you do not need to handle concurrent writes —
those go through admin).
