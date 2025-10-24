
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator, ConfigDict
import sqlite3
from datetime import datetime
from typing import Optional, List

# Configuración
DB_NAME = "tareas.db"

# ============== INICIALIZACIÓN DE BD ==============

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT DEFAULT 'media',
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente")


def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ============== MODELOS PYDANTIC ==============

class TareaBase(BaseModel):
    descripcion: str
    estado: str = "pendiente"
    prioridad: str = "media"
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()
    
    @field_validator('estado')
    @classmethod
    def estado_valido(cls, v):
        estados_validos = ["pendiente", "en_progreso", "completada"]
        if v not in estados_validos:
            raise ValueError(f"Estado debe ser uno de: {', '.join(estados_validos)}")
        return v
    
    @field_validator('prioridad')
    @classmethod
    def prioridad_valida(cls, v):
        prioridades_validas = ["baja", "media", "alta"]
        if v not in prioridades_validas:
            raise ValueError(f"Prioridad debe ser una de: {', '.join(prioridades_validas)}")
        return v


class TareaResponse(TareaBase):
    id: int
    fecha_creacion: str


# ============== APLICACIÓN FASTAPI ==============

app = FastAPI(title="API de Tareas", version="1.0.0")

# Inicializar BD al cargar el módulo
init_db()


# ============== ENDPOINTS ==============

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "nombre": "API de Tareas",
        "version": "1.0.0",
        "descripcion": "API para gestionar tareas con persistencia en SQLite",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "GET /tareas/resumen": "Obtener resumen de tareas",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas",
            "DELETE /tareas/{id}": "Eliminar una tarea"
        }
    }


@app.post("/tareas", status_code=201, response_model=TareaResponse)
async def crear_tarea(tarea: TareaBase):
    """Crear una nueva tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "fecha_creacion": fecha_creacion
    }


@app.get("/tareas", response_model=List[TareaResponse])
async def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc")
):
    """Obtener todas las tareas con filtros opcionales"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    # Filtro por estado
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    # Filtro por texto en descripción
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    # Filtro por prioridad
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    # Ordenamiento
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(t) for t in tareas]


@app.get("/tareas/resumen")
async def obtener_resumen():
    """Obtener un resumen de las tareas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    # Tareas por estado
    cursor.execute("""
        SELECT estado, COUNT(*) 
        FROM tareas 
        GROUP BY estado
    """)
    por_estado = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Tareas por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) 
        FROM tareas 
        GROUP BY prioridad
    """)
    por_prioridad = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    # Asegurar que todos los estados y prioridades aparezcan en el resumen
    estados_validos = ["pendiente", "en_progreso", "completada"]
    prioridades_validas = ["baja", "media", "alta"]
    
    for estado in estados_validos:
        if estado not in por_estado:
            por_estado[estado] = 0
    
    for prioridad in prioridades_validas:
        if prioridad not in por_prioridad:
            por_prioridad[prioridad] = 0
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


@app.put("/tareas/completar_todas")
async def completar_todas_tareas():
    """Marcar todas las tareas como completadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tareas 
        SET estado = 'completada'
        WHERE estado != 'completada'
    """)
    
    tareas_actualizadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return {
        "mensaje": f"{tareas_actualizadas} tareas marcadas como completadas"
    }


@app.put("/tareas/{tarea_id}", response_model=TareaResponse)
async def actualizar_tarea(tarea_id: int, tarea_actualizada: TareaBase):
    """Actualizar una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": f"Tarea con id {tarea_id} no encontrada"}
        )
    
    # Actualizar la tarea
    cursor.execute("""
        UPDATE tareas 
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (tarea_actualizada.descripcion, tarea_actualizada.estado, 
          tarea_actualizada.prioridad, tarea_id))
    
    conn.commit()
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea_actualizada.descripcion,
        "estado": tarea_actualizada.estado,
        "prioridad": tarea_actualizada.prioridad,
        "fecha_creacion": tarea_existente['fecha_creacion']
    }


@app.delete("/tareas/{tarea_id}")
async def eliminar_tarea(tarea_id: int):
    """Eliminar una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": f"Tarea con id {tarea_id} no encontrada"}
        )
    
    # Eliminar la tarea
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {
        "mensaje": f"Tarea {tarea_id} eliminada correctamente"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)