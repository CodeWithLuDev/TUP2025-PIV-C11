##  TP3 – API de Tareas con Persistencia en SQLite

Este proyecto implementa una API REST usando **FastAPI** y **SQLite** para manejar tareas de manera persistente.
Es una mejora del TP2, ya que ahora las tareas se guardan en un archivo real **tareas.db**
---

## 🚀 Cómo ejecutar el proyecto

### Instalar dependencias
```bash
pip install fastapi uvicorn
```

### Ejecutar el servidor
```bash
uvicorn main:app --reload
```

### Acceder a la documentación interactiva
```
http://127.0.0.1:8000/docs
```

---

##  Base de Datos

El archivo `tareas.db` se genera automáticamente al iniciar la API.

La tabla creada es:

```sql
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL,
    prioridad TEXT NOT NULL,
    fecha_creacion TEXT
)
```

---

##  Endpoints

###  Crear tarea — POST /tareas
```json
{
  "descripcion": "Estudiar",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

###  Listar tareas — GET /tareas  
Con filtros opcionales:
- `?estado=pendiente`
- `?prioridad=alta`

###  Obtener tarea por ID — GET /tareas/{id}

###  Modificar tarea — PUT /tareas/{id}

###  Eliminar tarea — DELETE /tareas/{id}

---

##  Código usado en main.py

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI()

class TareaBase(BaseModel):
    descripcion: str
    estado: str
    prioridad: str

def init_db():
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        prioridad TEXT NOT NULL,
        fecha_creacion TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()
```

---

## Testeo del TP

### Ejecutar todos los tests
```bash
pytest test_TP3.py -v
```

### Ejecutar solo un test puntual
```bash
pytest test_TP3.py::test_07_crear_tarea_exitosamente -v
```

---

## Persistencia

Si creás tareas, luego apagás el servidor y después lo volvés a iniciar,  
las tareas siguen ahí porque se guardan en **tareas.db** de manera persistente.


