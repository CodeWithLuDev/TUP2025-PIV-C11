from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from contextlib import asynccontextmanager
import sqlite3
from datetime import datetime

# ============================================
# MODELOS DE DATOS (usando Pydantic)
# ============================================

class TareaBase(BaseModel):
    """Modelo base para crear/actualizar tareas"""
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(
        default="pendiente",
        description="Estado de la tarea"
    )
    prioridad: Literal["baja", "media", "alta"] = Field(
        default="media",
        description="Prioridad de la tarea"
    )
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion_no_vacia(cls, v: str) -> str:
        """Valida que la descripción no sea solo espacios en blanco"""
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class TareaCrear(TareaBase):
    """Modelo para crear una tarea nueva"""
    pass

class TareaActualizar(BaseModel):
    """Modelo para actualizar una tarea (todos los campos opcionales)"""
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion_no_vacia(cls, v: Optional[str]) -> Optional[str]:
        """Valida que la descripción no sea solo espacios en blanco"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class Tarea(TareaBase):
    """Modelo completo de una tarea (incluye id y fecha)"""
    id: int
    fecha_creacion: str

class ResumenTareas(BaseModel):
    """Modelo para el resumen de tareas"""
    total_tareas: int
    por_estado: dict
    por_prioridad: dict

# ============================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ============================================

# IMPORTANTE: El test espera DB_NAME, no DATABASE_NAME
DB_NAME = "tareas.db"

def get_db_connection():
    """
    Crea y retorna una conexión a la base de datos SQLite.
    sqlite3.Row permite acceder a las columnas por nombre.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder como diccionario
    return conn

def init_db():
    """
    Inicializa la base de datos creando la tabla si no existe.
    Se ejecuta al iniciar la aplicación.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla tareas con la estructura exacta que espera el test
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

# ============================================
# CREAR LA APLICACIÓN FASTAPI
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestor de ciclo de vida de la aplicación"""
    # Código que se ejecuta al iniciar
    init_db()
    yield
    # Código que se ejecuta al cerrar (si es necesario)

app = FastAPI(
    title="API de Tareas Persistente",
    description="API REST para gestionar tareas con persistencia en SQLite",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================
# ENDPOINTS DE LA API
# ============================================

@app.get("/")
async def root():
    """Endpoint raíz de bienvenida - Estructura que espera el test"""
    return {
        "nombre": "API de Tareas con SQLite",
        "version": "1.0.0",
        "endpoints": {
            "GET /tareas": "Listar todas las tareas",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }

@app.get("/tareas/resumen", response_model=ResumenTareas)
async def obtener_resumen():
    """
    Obtiene un resumen con la cantidad de tareas por estado y prioridad.
    IMPORTANTE: Este endpoint debe ir ANTES de /tareas/{id}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contar total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    # Contar tareas por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    resultados_estado = cursor.fetchall()
    
    # Contar tareas por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        GROUP BY prioridad
    """)
    resultados_prioridad = cursor.fetchall()
    
    conn.close()
    
    # Inicializar contadores de estado
    por_estado = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    # Llenar los contadores de estado
    for row in resultados_estado:
        por_estado[row["estado"]] = row["cantidad"]
    
    # Inicializar contadores de prioridad
    por_prioridad = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    
    # Llenar los contadores de prioridad
    for row in resultados_prioridad:
        por_prioridad[row["prioridad"]] = row["cantidad"]
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.put("/tareas/completar_todas")
async def completar_todas_tareas():
    """
    Marca todas las tareas como completadas.
    IMPORTANTE: Este endpoint debe ir ANTES de /tareas/{id}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Actualizar todas las tareas a completada
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    filas_afectadas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        "mensaje": f"Se han completado {filas_afectadas} tareas exitosamente"
    }

@app.get("/tareas", response_model=list[Tarea])
async def listar_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query("asc")
):
    """
    Lista todas las tareas con filtros opcionales:
    - estado: Filtrar por estado
    - texto: Buscar en la descripción (búsqueda insensible a mayúsculas)
    - prioridad: Filtrar por prioridad
    - orden: Ordenar por fecha (asc o desc)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir la consulta SQL dinámicamente
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    # Agregar filtro por estado
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    # Agregar filtro por texto en descripción (case insensitive)
    if texto:
        query += " AND LOWER(descripcion) LIKE LOWER(?)"
        params.append(f"%{texto}%")
    
    # Agregar filtro por prioridad
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    # Agregar ordenamiento
    query += f" ORDER BY fecha_creacion {orden.upper()}"
    
    # Ejecutar consulta
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    # Convertir resultados a lista de diccionarios
    return [dict(tarea) for tarea in tareas]

@app.post("/tareas", response_model=Tarea, status_code=201)
async def crear_tarea(tarea: TareaCrear):
    """
    Crea una nueva tarea en la base de datos.
    La validación de datos se hace automáticamente por Pydantic.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener fecha y hora actual con microsegundos para mayor precisión
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    # Insertar la tarea en la base de datos
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual))
    
    # Obtener el ID de la tarea recién creada
    tarea_id = cursor.lastrowid
    conn.commit()
    
    # Obtener la tarea completa para devolverla
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return dict(nueva_tarea)

@app.put("/tareas/{id}", response_model=Tarea)
async def actualizar_tarea(id: int, tarea_actualizar: TareaActualizar):
    """
    Actualiza una tarea existente.
    Solo se actualizan los campos que se envían en el request.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        # El test espera que el detail contenga la palabra "error"
        raise HTTPException(
            status_code=404, 
            detail={"error": f"Tarea con id {id} no encontrada"}
        )
    
    # Construir la consulta de actualización solo con los campos proporcionados
    campos_actualizar = []
    valores = []
    
    if tarea_actualizar.descripcion is not None:
        campos_actualizar.append("descripcion = ?")
        valores.append(tarea_actualizar.descripcion)
    
    if tarea_actualizar.estado is not None:
        campos_actualizar.append("estado = ?")
        valores.append(tarea_actualizar.estado)
    
    if tarea_actualizar.prioridad is not None:
        campos_actualizar.append("prioridad = ?")
        valores.append(tarea_actualizar.prioridad)
    
    # Si no hay campos para actualizar, devolver la tarea sin cambios
    if not campos_actualizar:
        conn.close()
        return dict(tarea_existente)
    
    # Agregar el ID al final de los valores
    valores.append(id)
    
    # Ejecutar la actualización
    query = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = ?"
    cursor.execute(query, valores)
    conn.commit()
    
    # Obtener la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return dict(tarea_actualizada)

@app.delete("/tareas/{id}")
async def eliminar_tarea(id: int):
    """
    Elimina una tarea de la base de datos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        # El test espera que el detail contenga la palabra "error"
        raise HTTPException(
            status_code=404, 
            detail={"error": f"Tarea con id {id} no encontrada"}
        )
    
    # Eliminar la tarea
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": f"Tarea {id} eliminada correctamente"}
