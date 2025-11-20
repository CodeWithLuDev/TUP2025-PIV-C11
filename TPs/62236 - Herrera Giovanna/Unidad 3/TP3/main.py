from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime

app = FastAPI()

#   MODELOS Pydantic
class TareaBase(BaseModel):
    descripcion: str
    estado: str
    prioridad: str

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

#  FUNCIÓN PARA CONECTAR A LA bd
def get_db():
    conn = sqlite3.connect("tareas.db")
    conn.row_factory = sqlite3.Row
    return conn

#CREAR TABLA SI NO EXISTE
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Ejecutar automáticamente al iniciar
init_db()

#CREAR TAREA (POST)
@app.post("/tareas")
def crear_tarea(tarea: TareaBase):
    if tarea.estado not in ["pendiente", "en_progreso", "completada"]:
        raise HTTPException(status_code=400, detail="Estado inválido")

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual))

    conn.commit()
    conn.close()

    return {"mensaje": "Tarea creada con éxito"}
#      OBTENER TAREAS (GET)
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = None
):
    query = "SELECT * FROM tareas WHERE 1=1"
    valores = []

    if estado:
        query += " AND estado = ?"
        valores.append(estado)

    if texto:
        query += " AND descripcion LIKE ?"
        valores.append(f"%{texto}%")

    if prioridad:
        query += " AND prioridad = ?"
        valores.append(prioridad)

    if orden in ["asc", "desc"]:
        query += f" ORDER BY fecha_creacion {orden.upper()}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, valores)
    filas = cursor.fetchall()
    conn.close()

    return [dict(fila) for fila in filas]

#MODIFICAR TAREA (PUT)
@app.put("/tareas/{id}")
def modificar_tarea(id: int, tarea: TareaBase):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existente = cursor.fetchone()

    if not existente:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    cursor.execute("""
        UPDATE tareas 
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, id))

    conn.commit()
    conn.close()

    return {"mensaje": "Tarea modificada"}
#ELIMINAR TAREA (DELETE)
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existente = cursor.fetchone()

    if not existente:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": "Tarea eliminada"}
# RESUMEN 
@app.get("/tareas/resumen")
def resumen():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    datos = cursor.fetchall()
    conn.close()

    return {fila["estado"]: fila["cantidad"] for fila in datos}