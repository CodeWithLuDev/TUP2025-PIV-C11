# TP3.2: Mini API de Tareas con FastAPI

## 🚀 Instalación

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📡 Endpoints

- GET `/tareas`
  - Query params opcionales: `estado`, `texto`
- POST `/tareas`
- PUT `/tareas/{id}`
- DELETE `/tareas/{id}`
- GET `/tareas/resumen`
- PUT `/tareas/completar_todas`

## 🧾 Modelo de Tarea

```json
{
  "id": 1,
  "descripcion": "Mi tarea",
  "estado": "pendiente",
  "fecha_creacion": "2025-10-06T12:00:00Z"
}
```

Estados válidos: `pendiente` | `en_progreso` | `completada`.

## 🧪 Tests locales (opcional)

```bash
python -m pytest -q
```
