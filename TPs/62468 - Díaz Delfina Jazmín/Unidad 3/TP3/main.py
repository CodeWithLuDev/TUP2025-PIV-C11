# Importamos las herramientas que necesitamos
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import sqlite3
from datetime import datetime
from contextlib import asynccontextmanager

# Nombre de nuestro archivo de base de datos
DB_NAME = "tareas.db"

# ===== FUNCIONES DE BASE DE DATOS =====

def get_db_connection():
    """
    Abre una conexión a la base de datos.
    Es como abrir el cuaderno donde guardamos las tareas.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Esto nos permite acceder a los datos por nombre
    return conn

def init_db():
    """
    Crea la tabla de tareas si no existe.
    Es como preparar el cuaderno con las columnas necesarias la primera vez.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Esta es la instrucción SQL que crea la tabla
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    conn.commit()  # Guardamos los cambios
    conn.close()   # Cerramos el cuaderno

# ===== LIFESPAN (REEMPLAZO MODERNO DE ON_EVENT) =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar el servidor.
    """
    # Código que se ejecuta al INICIAR
    init_db()
    print("✅ Base de datos inicializada correctamente")
    yield
    # Código que se ejecuta al CERRAR (si lo necesitáramos)

# Creamos nuestra aplicación con el lifespan
app = FastAPI(title="API de Tareas Persistente", lifespan=lifespan)

# ===== MODELOS DE DATOS =====

class TareaCrear(BaseModel):
    """Formulario para crear una nueva tarea"""
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: str = Field(default="pendiente", pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(default="media", pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        """
        Valida que la descripción no sea solo espacios en blanco.
        """
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v.strip()

class TareaActualizar(BaseModel):
    """Formulario para actualizar una tarea existente"""
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")
    prioridad: Optional[str] = Field(None, pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        """Valida que la descripción no sea solo espacios"""
        if v is not None:
            if v.strip() == "":
                raise ValueError('La descripción no puede estar vacía o contener solo espacios')
            return v.strip()
        return v

# ===== ENDPOINTS =====

@app.get("/")
def root():
    """Página de bienvenida"""
    return {
        "mensaje": "API de Tareas",
        "version": "1.0",
        "endpoints": {
            "tareas": "/tareas",
            "resumen": "/tareas/resumen"
        }
    }

@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Devuelve un resumen de cuántas tareas hay por cada estado y prioridad.
    Incluye el total general de tareas, desglose por estado y por prioridad.
    """
    conn = get_db_connection()
    
    # Contamos las tareas por estado
    resumen_estados = conn.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """).fetchall()
    
    # Contamos las tareas por prioridad
    resumen_prioridades = conn.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        GROUP BY prioridad
    """).fetchall()
    
    # Contamos el total de tareas
    total = conn.execute("SELECT COUNT(*) as total FROM tareas").fetchone()
    
    conn.close()
    
    # Creamos el objeto por_estado
    por_estado = {}
    for fila in resumen_estados:
        por_estado[fila['estado']] = fila['cantidad']
    
    # Aseguramos que todos los estados estén presentes
    for estado in ['pendiente', 'en_progreso', 'completada']:
        if estado not in por_estado:
            por_estado[estado] = 0
    
    # Creamos el objeto por_prioridad
    por_prioridad = {}
    for fila in resumen_prioridades:
        por_prioridad[fila['prioridad']] = fila['cantidad']
    
    # Aseguramos que todas las prioridades estén presentes
    for prioridad in ['baja', 'media', 'alta']:
        if prioridad not in por_prioridad:
            por_prioridad[prioridad] = 0
    
    # Construimos la respuesta con la estructura esperada
    return {
        "total_tareas": total['total'],
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    texto: Optional[str] = None,
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    orden: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    """
    Obtiene todas las tareas con filtros opcionales.
    """
    conn = get_db_connection()
    
    # Construimos la consulta SQL de manera dinámica
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    # IMPORTANTE: Ordenamos por ID también para asegurar consistencia
    # cuando las fechas son iguales
    if orden.lower() == "desc":
        query += " ORDER BY fecha_creacion DESC, id DESC"
    else:
        query += " ORDER BY fecha_creacion ASC, id ASC"
    
    tareas = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCrear):
    """Crea una nueva tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtenemos la fecha y hora actual con precisión de microsegundos
    # Esto ayuda a evitar que dos tareas tengan exactamente la misma fecha
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual))
    
    conn.commit()
    nueva_tarea_id = cursor.lastrowid
    
    nueva_tarea = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", 
        (nueva_tarea_id,)
    ).fetchone()
    
    conn.close()
    
    return dict(nueva_tarea)

@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    """
    Marca todas las tareas como completadas.
    Es un endpoint especial para cambiar el estado de todas las tareas de una vez.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Actualizamos todas las tareas que NO estén completadas
    cursor.execute("""
        UPDATE tareas 
        SET estado = 'completada' 
        WHERE estado != 'completada'
    """)
    
    tareas_actualizadas = cursor.rowcount  # Cuántas tareas se modificaron
    conn.commit()
    
    # Obtenemos todas las tareas para devolverlas
    tareas = conn.execute("SELECT * FROM tareas").fetchall()
    conn.close()
    
    return {
        "mensaje": "Todas las tareas han sido marcadas como completadas",
        "tareas_actualizadas": tareas_actualizadas,
        "tareas": [dict(tarea) for tarea in tareas]
    }

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaActualizar):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tarea_existente = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", 
        (id,)
    ).fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(
            status_code=404, 
            detail={"error": "Tarea no encontrada"}
        )
    
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
        return dict(tarea_existente)
    
    valores.append(id)
    
    query = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = ?"
    cursor.execute(query, valores)
    conn.commit()
    
    tarea_actualizada = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", 
        (id,)
    ).fetchone()
    
    conn.close()
    
    return dict(tarea_actualizada)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tarea = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", 
        (id,)
    ).fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(
            status_code=404, 
            detail={"error": "Tarea no encontrada"}
        )
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada exitosamente", "id": id}