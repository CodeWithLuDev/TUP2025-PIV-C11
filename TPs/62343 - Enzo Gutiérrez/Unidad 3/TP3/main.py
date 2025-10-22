import sqlite3
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

DB_NAME = "tareas.db"

# ============== MODELOS DE VALIDACIÓN ==============

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: str = Field(default="pendiente", pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(default="media", pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, valor):
        if not valor or not valor.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return valor

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")
    prioridad: Optional[str] = Field(None, pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, valor):
        if valor is not None and (not valor or not valor.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return valor

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

# ============== GESTIÓN DE BASE DE DATOS ==============

def init_db():
    """Inicializa la estructura de la base de datos"""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    conexion.commit()
    conexion.close()
    print("Base de datos inicializada correctamente")

def obtener_conexion():
    """Establece conexión con la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def fila_a_diccionario(fila):
    """Convierte una fila de SQLite a diccionario"""
    return dict(fila) if fila else None

# ============== CICLO DE VIDA DE LA APLICACIÓN ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Servidor iniciado - Base de datos lista")
    yield
    print("Servidor detenido")

# ============== APLICACIÓN FASTAPI ==============

app = FastAPI(
    title="API de Tareas Persistente",
    description="TP3 - Gestión de tareas con SQLite",
    version="1.0.0",
    lifespan=lifespan
)

# ============== ENDPOINTS ==============

@app.get("/")
def raiz():
    return {
        "nombre": "API de Tareas - TP3",
        "version": "1.0.0",
        "endpoints": [
            "GET /tareas - Listar todas las tareas",
            "POST /tareas - Crear una tarea",
            "PUT /tareas/{id} - Actualizar una tarea",
            "DELETE /tareas/{id} - Eliminar una tarea",
            "GET /tareas/resumen - Resumen por estado y prioridad",
            "PUT /tareas/completar_todas - Completar todas las tareas"
        ]
    }

@app.get("/tareas/resumen")
def resumen_tareas():
    """Genera resumen estadístico de tareas por estado y prioridad"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    conteo_estados = cursor.fetchall()
    
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        GROUP BY prioridad
    """)
    conteo_prioridades = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]
    
    conn.close()
    
    estados = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    prioridades = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    
    for registro in conteo_estados:
        estados[registro["estado"]] = registro["cantidad"]
    
    for registro in conteo_prioridades:
        prioridades[registro["prioridad"]] = registro["cantidad"]
    
    return {
        "total_tareas": total_tareas,
        "por_estado": estados,
        "por_prioridad": prioridades
    }

@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    """Marca todas las tareas como completadas"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    cantidad_actualizada = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        "mensaje": f"Se completaron {cantidad_actualizada} tareas",
        "tareas_actualizadas": cantidad_actualizada
    }

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """Crea una nueva tarea en la base de datos"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, timestamp)
    )
    
    conn.commit()
    nuevo_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (nuevo_id,))
    tarea_creada = cursor.fetchone()
    conn.close()
    
    return fila_a_diccionario(tarea_creada)

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    texto: Optional[str] = None,
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    orden: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    """
    Obtiene lista de tareas con filtros opcionales:
    - estado: filtrar por estado específico
    - texto: búsqueda en descripción
    - prioridad: filtrar por nivel de prioridad
    - orden: ordenar por ID (asc o desc)
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    sql = "SELECT * FROM tareas WHERE 1=1"
    parametros = []
    
    if estado:
        sql += " AND estado = ?"
        parametros.append(estado)
    
    if texto:
        sql += " AND descripcion LIKE ?"
        parametros.append(f"%{texto}%")
    
    if prioridad:
        sql += " AND prioridad = ?"
        parametros.append(prioridad)
    
    sql += f" ORDER BY id {'DESC' if orden == 'desc' else 'ASC'}"
    
    cursor.execute(sql, parametros)
    resultados = cursor.fetchall()
    conn.close()
    
    return [fila_a_diccionario(fila) for fila in resultados]

@app.get("/tareas/{id}")
def obtener_tarea(id: int):
    """Obtiene una tarea por su ID"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    resultado = cursor.fetchone()
    conn.close()
    
    if not resultado:
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    return fila_a_diccionario(resultado)

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Actualiza campos de una tarea existente"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existe = cursor.fetchone()
    
    if not existe:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    campos_actualizar = []
    valores = []
    
    if tarea.descripcion is not None:
        campos_actualizar.append("descripcion = ?")
        valores.append(tarea.descripcion)
    
    if tarea.estado is not None:
        campos_actualizar.append("estado = ?")
        valores.append(tarea.estado)
    
    if tarea.prioridad is not None:
        campos_actualizar.append("prioridad = ?")
        valores.append(tarea.prioridad)
    
    if not campos_actualizar:
        conn.close()
        raise HTTPException(status_code=400, detail={"error": "No se enviaron campos para actualizar"})
    
    valores.append(id)
    sql_update = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = ?"
    
    cursor.execute(sql_update, valores)
    conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_modificada = cursor.fetchone()
    conn.close()
    
    return fila_a_diccionario(tarea_modificada)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea de la base de datos"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente", "id": id}