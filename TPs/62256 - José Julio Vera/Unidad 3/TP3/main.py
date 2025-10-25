# main.py
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Body, status
from pydantic import BaseModel, Field, conlist
from typing import List, Optional, Literal, Dict, Any, Tuple
from datetime import datetime

# ------------------------------------------------------------------------------
# 1. Configuración y Modelos de Pydantic
# ------------------------------------------------------------------------------

# Tipos Literal para validación estricta (Pydantic)
EstadoTarea = Literal["pendiente", "en_progreso", "completada"]
PrioridadTarea = Literal["baja", "media", "alta"]
Ordenamiento = Literal["asc", "desc"]

# Modelo de datos de la Tarea (para la respuesta de la API)
class Tarea(BaseModel):
    id: int = Field(..., gt=0)
    descripcion: str = Field(..., min_length=1)
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_creacion: str # Se mantiene como string (ISO format) para simplicidad con SQLite

# Modelo de entrada para la creación/actualización de tareas
class TareaIn(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: EstadoTarea = Field("pendiente")
    prioridad: PrioridadTarea = Field("media")

# Constantes
DB_NAME = "tareas.db"
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
PRIORIDADES_VALIDAS = {"baja", "media", "alta"}

# Inicialización de la aplicación
app = FastAPI(
    title="Mini API de Tareas (TP3 - SQLite)",
    description="CRUD persistente con base de datos SQLite.",
    version="3.0.0"
)

# ------------------------------------------------------------------------------
# 2. Funciones de Base de Datos
# ------------------------------------------------------------------------------

def get_db_connection():
    """Crea y devuelve una conexión a la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
    return conn

def init_db():
    """Crea la tabla 'tareas' si no existe."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear la tabla con las columnas requeridas (id AUTOINCREMENT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

# Ejecutar la inicialización de la DB al inicio de la aplicación
# NOTA: En un entorno de producción, esto se haría en un evento startup de FastAPI.
init_db()


def row_to_tarea(row: sqlite3.Row) -> Tarea:
    """Convierte una fila de la DB (sqlite3.Row) a un modelo Pydantic Tarea."""
    # SQLite guarda la fecha como string, la usamos directamente
    return Tarea(
        id=row["id"],
        descripcion=row["descripcion"],
        estado=row["estado"],
        prioridad=row["prioridad"],
        fecha_creacion=row["fecha_creacion"]
    )

# ------------------------------------------------------------------------------
# 3. Endpoints de la API
# ------------------------------------------------------------------------------

@app.get("/tareas", response_model=List[Tarea], summary="Obtener todas las tareas (con filtros y ordenamiento)")
def get_tareas(
    estado: Optional[EstadoTarea] = Query(None, description="Filtra tareas por estado"),
    texto: Optional[str] = Query(None, description="Busca tareas por contenido en la descripción"),
    prioridad: Optional[PrioridadTarea] = Query(None, description="Filtra tareas por prioridad"),
    orden: Optional[Ordenamiento] = Query(None, description="Ordena por fecha_creacion ('asc' o 'desc')")
) -> List[Tarea]:
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Construcción dinámica de la consulta SQL
    query = "SELECT * FROM tareas WHERE 1=1"
    params: List[Any] = []

    if estado:
        query += " AND estado = ?"
        params.append(estado)

    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)

    if texto:
        # Uso de LIKE para búsqueda parcial (insensible a mayúsculas/minúsculas)
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")

    if orden:
        order_direction = "DESC" if orden == "desc" else "ASC"
        query += f" ORDER BY fecha_creacion {order_direction}"
    
    # Ejecución y mapeo de resultados
    cursor.execute(query, params)
    tareas_rows = cursor.fetchall()
    conn.close()
    
    return [row_to_tarea(row) for row in tareas_rows]


@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED, summary="Crear una nueva tarea")
def create_tarea(
    tarea_in: TareaIn = Body(..., description="Datos de la nueva tarea.")
) -> Tarea:
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Pydantic ya validó que la descripción no está vacía y que estado/prioridad son válidos
    
    now_iso = datetime.now().isoformat()
    
    # Guardar en la DB
    cursor.execute(
        """
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) 
        VALUES (?, ?, ?, ?);
        """,
        (tarea_in.descripcion, tarea_in.estado, tarea_in.prioridad, now_iso)
    )
    
    new_id = cursor.lastrowid
    conn.commit()
    
    # Recuperar la tarea creada para la respuesta
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (new_id,))
    new_tarea_row = cursor.fetchone()
    conn.close()
    
    return row_to_tarea(new_tarea_row)


@app.put("/tareas/{id}", response_model=Tarea, summary="Actualizar una tarea existente")
def update_tarea(
    id: int,
    tarea_in: TareaIn = Body(..., description="Nuevos datos de la tarea."),
) -> Tarea:
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Actualizar la DB
    cursor.execute(
        """
        UPDATE tareas
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?;
        """,
        (tarea_in.descripcion, tarea_in.estado, tarea_in.prioridad, id)
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"error": f"Tarea con id {id} no encontrada"}
        )

    conn.commit()
    
    # Recuperar la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    updated_tarea_row = cursor.fetchone()
    conn.close()
    
    return row_to_tarea(updated_tarea_row)


@app.delete("/tareas/{id}", status_code=status.HTTP_200_OK, summary="Eliminar una tarea")
def delete_tarea(id: int) -> Dict[str, str]:
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"error": f"Tarea con id {id} no encontrada"}
        )

    conn.commit()
    conn.close()
    return {"message": f"Tarea con id {id} eliminada exitosamente"}


# ------------------------------------------------------------------------------
# 4. Implementación de Mejoras (Obligatorio)
# ------------------------------------------------------------------------------

@app.get("/tareas/resumen", summary="Contador de tareas por estado")
def get_resumen_tareas() -> Dict[str, int]:
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Consulta SQL para agrupar y contar por estado
    cursor.execute("""
        SELECT estado, COUNT(id) as count 
        FROM tareas 
        GROUP BY estado;
    """)
    results = cursor.fetchall()
    conn.close()
    
    # Inicializar con 0 para todos los estados posibles
    resumen: Dict[str, int] = {estado: 0 for estado in ESTADOS_VALIDOS}
    
    # Rellenar con los resultados de la DB
    for row in results:
        estado = row["estado"]
        count = row["count"]
        if estado in resumen:
             resumen[estado] = count

    return resumen


@app.delete("/limpiar_db", status_code=status.HTTP_200_OK, include_in_schema=False)
def limpiar_db():
    """Endpoint de ayuda para testing: Elimina todos los datos de la tabla."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tareas")
    cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'tareas'") # Resetear auto-incremento
    conn.commit()
    conn.close()
    return {"message": "Base de datos de tareas limpiada y contador reiniciado"}