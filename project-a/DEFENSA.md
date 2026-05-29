**## Cómo verificar la entrega**

```bash
# Levantar Postgres (si no está corriendo) + ejecutar TODA la suite de defensa
./scripts/run_all_defense_tests.sh

# Solo la lógica de negocio (inventory/capacity)
./scripts/run_inventory_tests.sh
```

Una entrega correcta debe terminar con:

```
======== N passed in Xs ========
```

sin tests fallidos ni saltados.

# Business Logic
Implement this business logic

Inventory / capacity enforcement. When the API returns availability for the main resource. The
computation must be correct under concurrent reads (you do not need to handle concurrent writes —
those go through admin).