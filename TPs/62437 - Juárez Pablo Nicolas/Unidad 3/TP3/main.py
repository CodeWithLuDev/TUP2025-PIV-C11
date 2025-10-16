from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import sqlite3
from contextlib import contextmanager

app = FastAPI()

# Nombre de la base de datos (necesario para los tests)
DB_NAME = "tareas.db"

# Enum para validar los estados válidos
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Enum para validar prioridades
class PrioridadTarea(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

# Modelo de entrada
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1, description="La descripción no puede estar vacía")
    estado: EstadoTarea = EstadoTarea.pendiente
    prioridad: PrioridadTarea = PrioridadTarea.media
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v.strip()

# Modelo para actualización
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[EstadoTarea] = None
    prioridad: Optional[PrioridadTarea] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v.strip() if v else v

# Modelo de salida con ID y fecha
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_creacion: str

# Context manager para conexiones a la base de datos
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Inicializar la base de datos
def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL DEFAULT 'media',
                fecha_creacion TEXT NOT NULL
            )
        ''')
        conn.commit()

# Limpiar la base de datos (útil para tests)
def clear_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tareas')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="tareas"')
        conn.commit()

# Ejecutar init_db al iniciar la aplicación
@app.on_event("startup")
def startup_event():
    init_db()

# Endpoint raíz - Información de la API
@app.get("/")
def raiz():
    return {
        "nombre": "API de Gestión de Tareas",
        "version": "1.0",
        "descripcion": "API para administrar tareas con persistencia en SQLite",
        "endpoints": {
            "GET /": "Información de la API",
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas por estado",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }

# Endpoint para limpiar la base de datos (útil para tests)
@app.delete("/tareas/limpiar")
def limpiar_tareas():
    clear_db()
    return {"mensaje": "Todas las tareas han sido eliminadas"}

# Crear una nueva tarea
@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaBase):
    fecha_creacion = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
        ''', (tarea.descripcion, tarea.estado.value, tarea.prioridad.value, fecha_creacion))
        
        nueva_id = cursor.lastrowid
        
        return Tarea(
            id=nueva_id,
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            prioridad=tarea.prioridad,
            fecha_creacion=fecha_creacion
        )

# Contador de tareas por estado
@app.get("/tareas/resumen")
def resumen_tareas():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Contar por estado
        cursor.execute('''
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        ''')
        
        por_estado = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        
        for row in cursor.fetchall():
            por_estado[row['estado']] = row['cantidad']
        
        # Contar por prioridad
        cursor.execute('''
            SELECT prioridad, COUNT(*) as cantidad
            FROM tareas
            GROUP BY prioridad
        ''')
        
        por_prioridad = {
            "baja": 0,
            "media": 0,
            "alta": 0
        }
        
        for row in cursor.fetchall():
            por_prioridad[row['prioridad']] = row['cantidad']
        
        # Agregar total de tareas
        cursor.execute('SELECT COUNT(*) as total FROM tareas')
        total = cursor.fetchone()['total']
        
        return {
            "total_tareas": total,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

# Marcar todas las tareas como completadas
@app.put("/tareas/completar_todas")
def completar_todas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as total FROM tareas')
        total = cursor.fetchone()['total']
        
        if total == 0:
            return {"mensaje": "No hay tareas para completar"}
        
        cursor.execute('''
            UPDATE tareas
            SET estado = ?
        ''', (EstadoTarea.completada.value,))
        
        return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

# Obtener todas las tareas con filtros opcionales
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[EstadoTarea] = None,
    texto: Optional[str] = None,
    prioridad: Optional[PrioridadTarea] = None,
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = ?"
            params.append(estado.value)
        
        if texto:
            query += " AND descripcion LIKE ?"
            params.append(f"%{texto}%")
        
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad.value)
        
        # Ordenamiento por fecha
        if orden:
            if orden == "asc":
                query += " ORDER BY fecha_creacion ASC"
            else:
                query += " ORDER BY fecha_creacion DESC"
        else:
            query += " ORDER BY id ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        tareas = []
        for row in rows:
            tareas.append(Tarea(
                id=row['id'],
                descripcion=row['descripcion'],
                estado=row['estado'],
                prioridad=row['prioridad'],
                fecha_creacion=row['fecha_creacion']
            ))
        
        return tareas

# Editar una tarea existente
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si la tarea existe
        cursor.execute('SELECT * FROM tareas WHERE id = ?', (id,))
        tarea_actual = cursor.fetchone()
        
        if not tarea_actual:
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        
        # Actualizar solo los campos proporcionados
        updates = []
        params = []
        
        if tarea.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(tarea.descripcion)
        
        if tarea.estado is not None:
            updates.append("estado = ?")
            params.append(tarea.estado.value)
        
        if tarea.prioridad is not None:
            updates.append("prioridad = ?")
            params.append(tarea.prioridad.value)
        
        if updates:
            query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
            params.append(id)
            cursor.execute(query, params)
        
        # Obtener la tarea actualizada
        cursor.execute('SELECT * FROM tareas WHERE id = ?', (id,))
        tarea_actualizada = cursor.fetchone()
        
        return Tarea(
            id=tarea_actualizada['id'],
            descripcion=tarea_actualizada['descripcion'],
            estado=tarea_actualizada['estado'],
            prioridad=tarea_actualizada['prioridad'],
            fecha_creacion=tarea_actualizada['fecha_creacion']
        )

# Eliminar una tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si la tarea existe
        cursor.execute('SELECT * FROM tareas WHERE id = ?', (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        
        cursor.execute('DELETE FROM tareas WHERE id = ?', (id,))
        
        return {"mensaje": "Tarea eliminada correctamente"}