from fastapi import FastAPI,HTTPException, Query 
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3
from contextlib import contextmanager


app = FastAPI(title="API de Tareas Persistentes - TP3" , version="2.0.0")

DB_NAME = "tareas.db"

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
        
def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS tareas (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          descripcion TEXT NOT NULL,
                          estado TEXT NOT NULL,
                          prioridad TEXT NOT NULL DEFAULT 'media',
                          fecha_creacion TEXT NOT NULL 
                       )""")
        conn.commit()
    print("Base de datos inicializada correctamente.")
    
init_db()



class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente","en_progreso","completada"] =  "pendiente"
    prioridad: Literal["baja","media","alta"] = "media"
    
    
    @field_validator("descripcion")
    @classmethod
    def validar_descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripcion no puede estar vacia')
        return v.strip()
    
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente","en_progreso","completada"]] = None
    prioridad: Optional[Literal["baja","media","alta"]] = None
    
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Literal["pendiente","en_progreso","completada"]
    prioridad: Literal["baja","media","alta"] 
    fecha_creacion: str
    
    
def row_to_dict(row):
    return{
        "id":row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "fecha_creacion": row["fecha_creacion"]
    } 
    
@app.get("/")
def root():
    return{"message":"API de Tareas Persistentes - TP3",
           "version":"2.0.0",
           "endpoints": [
               "/tareas",
               "/tareas/resumen",
               "/tareas/completar_todas",
               "/tareas/{id}"
            ]
           }

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    texto: Optional[str]= Query(None, description="Buscar por texto en descripcion "),
    prioridad: Optional[str]= Query (None, description="Filtrar por prioridad"),
    orden: Optional[Literal["asc","desc"]] = Query(None, description="Ordenar por fecha de creacion")
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = " SELECT * FROM tareas WHERE 1=1"
        params = []
        #Filtrar por estado
        if estado:
            if estado not in ["pendiente","en_progreso","completada"]:
                raise HTTPException(
                    status_code=400,
                    detail={"error": f"Prioridad '{prioridad}' no valida. Debe ser: baja, media o alta."}
                )
            query += " AND estado = ?"
            params.append(estado)
        #Filtrar por prioridad
        if prioridad:
            if prioridad not in ["baja","media","alta"]:
                raise HTTPException(
                    status_code= 400,
                    detail={"error": f"Prioridad '{prioridad}' no valida. Debe ser: baja, media o alta."}
                )
            query += " AND prioridad = ?"
            params.append(prioridad)
        #Buscar por texto en descripcion  
        if texto:
            query += " AND descripcion LIKE ?"
            params.append(f"%{texto}%")
            
        #Ordenar por fecha
        if orden:
            if orden == "asc":
                query += " ORDER BY fecha_creacion ASC"
            else:
                query += " ORDER BY fecha_creacion DESC"
        else:
            query += " ORDER BY id ASC"
            
        cursor.execute(query,params)
        rows = cursor.fetchall()
        
        return [row_to_dict(row) for row in rows]
    
    
@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion))
        
        tarea_id = cursor.lastrowid
        
        #obtener la tarea recien creada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        
        return row_to_dict(row)
    
@app.get("/tareas/resumen")
def obtener_resumen():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Contar tareas por estado
        cursor.execute("""
                       SELECT estado, COUNT(*) as cantidad
                       FROM tareas
                       GROUP BY estado
                       """)
        rows_estado = cursor.fetchall()
        
        # Inicializar con ceros para estados
        por_estado = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        
        # Actualizar con los valores reales para estados
        for row in rows_estado:
            por_estado[row["estado"]] = row["cantidad"]
        
        # Contar tareas por prioridad
        cursor.execute("""
                       SELECT prioridad, COUNT(*) as cantidad
                       FROM tareas
                       GROUP BY prioridad
                       """)
        rows_prioridad = cursor.fetchall()
        
        # Inicializar con ceros para prioridades
        por_prioridad = {
            "baja": 0,
            "media": 0,
            "alta": 0
        }
        
        # Actualizar con los valores reales para prioridades
        for row in rows_prioridad:
            por_prioridad[row["prioridad"]] = row["cantidad"]
        
        # Calcular el total de tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()["total"]
        
        # Estructura de la respuesta
        resumen = {
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }
        
        return resumen
    
@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    with get_db() as conn:
        cursor = conn.cursor()
        
        #contar cuantas tareas no estan completadas
        cursor.execute("""
                       SELECT COUNT(*) as cantidad
                       FROM  tareas
                       WHERE estado != 'completada'
                       """)
        
        cantidad = cursor.fetchone()["cantidad"]
        
        if cantidad == 0:
            cursor.execute("SELECT COUNT(*) as total FROM  tareas")
            total = cursor.fetchone()["total"]
            
            if total == 0:
                return {
                    "mensaje": "No hay tareas para completar",
                    "tareas_actualizadas": 0
                }
            else:
                return {
                    "mensaje": "Todas las tareas ya estan completadas",
                    "tareas_actualizadas": 0
                }        
                
        #actualizar todas las tareas a completadas
        cursor.execute("""
                       UPDATE tareas 
                       SET estado = 'completada'
                       WHERE estado != 'completada'
                       """)
        
        return {
            "mensaje": f"Se completaron {cantidad} tareas",
            "tareas_actualizadas": cantidad
        }            
    
@app.get("/tareas/{id}")
def obtener_tarea(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tareas WHERE id = ?" , (id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail={"error": "La tarea no existe"}
            )
        
        return row_to_dict(row)
    
    
@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        
        #verificar que la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(
                status_code=404,
                detail={"error": "La tarea no existe"}
            )
            
        #validar y actualizar descripcion
        if tarea_update.descripcion is not None:
            desc_limpia = tarea_update.descripcion.strip()
            if not desc_limpia:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "La descripcion no puede estar vacia"}
                )
            cursor.execute(
                "UPDATE tareas SET  descripcion = ? WHERE id = ?",
                (desc_limpia, id)
            )                 
            
        #actualizar estado
        if tarea_update.estado is not None:
             cursor.execute(
                 "UPDATE tareas SET estado = ? WHERE id = ?",
                 (tarea_update.estado, id)
             )      
         
        #actualizar prioridad
        if tarea_update.prioridad is not None:
            cursor.execute(
                "UPDATE tareas SET prioridad = ? WHERE id = ?",
                (tarea_update.prioridad, id)
            )
            
        #obtener la tarea actualizada
        cursor.execute("SELECT * FROM tareas WHERE  id  = ?", (id,))
        row = cursor. fetchone()
        
        return row_to_dict(row)
    
    
@app.delete("/tareas/{id}")
def eliminar_tarea(id:int):
    with  get_db() as conn:
        cursor = conn.cursor()
        
        #verificar que la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(
                status_code=404,
                detail={"error": "La tarea no existe"}
            )
            
        #eliminar la tarea
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        
        return{
            "mensaje":"Tarea eliminada exitosamente",
            "tarea":row_to_dict(tarea)
        }            
