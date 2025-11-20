from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import sqlite3

from database import init_db, get_connection
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate

app = FastAPI(title="TP4 - Proyectos y Tareas")
init_db()


# PROYECTOS

@app.post("/proyectos")
def crear_proyecto(proyecto: ProyectoCreate):
    conn = get_connection()
    cursor = conn.cursor()

    if not proyecto.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

    cursor.execute("SELECT * FROM proyectos WHERE nombre=?", (proyecto.nombre,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Nombre de proyecto ya existe")

    fecha = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (proyecto.nombre, proyecto.descripcion, fecha)
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Proyecto creado exitosamente"}

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM proyectos"
    params = ()

    if nombre:
        query += " WHERE nombre LIKE ?"
        params = (f"%{nombre}%",)

    cursor.execute(query, params)
    proyectos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return proyectos

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cursor.execute("SELECT COUNT(*) as total_tareas FROM tareas WHERE proyecto_id=?", (id,))
    total_tareas = cursor.fetchone()["total_tareas"]

    result = dict(proyecto)
    result["total_tareas"] = total_tareas
    conn.close()
    return result

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    if proyecto.nombre:
        cursor.execute("SELECT * FROM proyectos WHERE nombre=? AND id!=?", (proyecto.nombre, id))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Nombre de proyecto ya existe")

    cursor.execute("""
        UPDATE proyectos SET nombre=COALESCE(?, nombre),
                             descripcion=COALESCE(?, descripcion)
        WHERE id=?
    """, (proyecto.nombre, proyecto.descripcion, id))
    conn.commit()
    conn.close()
    return {"mensaje": "Proyecto actualizado exitosamente"}

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cursor.execute("DELETE FROM proyectos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Proyecto eliminado con sus tareas asociadas"}


# TAREAS

@app.post("/proyectos/{proyecto_id}/tareas")
def crear_tarea(proyecto_id: int, tarea: TareaCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    fecha = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, proyecto_id, fecha)
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea creada exitosamente"}

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = Query("asc", regex="^(asc|desc)$")
):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tareas WHERE 1=1"
    params = []

    if estado:
        query += " AND estado=?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad=?"
        params.append(prioridad)
    if proyecto_id:
        query += " AND proyecto_id=?"
        params.append(proyecto_id)

    query += f" ORDER BY fecha_creacion {orden.upper()}"
    cursor.execute(query, tuple(params))
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(id: int, estado: Optional[str] = None, prioridad: Optional[str] = None, orden: Optional[str] = Query("asc", regex="^(asc|desc)$")):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    query = "SELECT * FROM tareas WHERE proyecto_id=?"
    params = [id]

    if estado:
        query += " AND estado=?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad=?"
        params.append(prioridad)

    query += f" ORDER BY fecha_creacion {orden.upper()}"
    cursor.execute(query, tuple(params))
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if tarea.proyecto_id:
        cursor.execute("SELECT * FROM proyectos WHERE id=?", (tarea.proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Proyecto_id no existe")

    cursor.execute("""
        UPDATE tareas SET
            descripcion = COALESCE(?, descripcion),
            estado = COALESCE(?, estado),
            prioridad = COALESCE(?, prioridad),
            proyecto_id = COALESCE(?, proyecto_id)
        WHERE id=?
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, tarea.proyecto_id, id))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea actualizada exitosamente"}

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    cursor.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada"}

# RESUMEN Y ESTADISTICAS

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cursor.execute("SELECT estado, COUNT(*) as total FROM tareas WHERE proyecto_id=? GROUP BY estado", (id,))
    por_estado = {row["estado"]: row["total"] for row in cursor.fetchall()}

    cursor.execute("SELECT prioridad, COUNT(*) as total FROM tareas WHERE proyecto_id=? GROUP BY prioridad", (id,))
    por_prioridad = {row["prioridad"]: row["total"] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id=?", (id,))
    total_tareas = cursor.fetchone()["total"]

    conn.close()
    return {
        "proyecto_id": proyecto["id"],
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total_proyectos FROM proyectos")
    total_proyectos = cursor.fetchone()["total_proyectos"]

    cursor.execute("SELECT COUNT(*) as total_tareas FROM tareas")
    total_tareas = cursor.fetchone()["total_tareas"]

    cursor.execute("SELECT estado, COUNT(*) as total FROM tareas GROUP BY estado")
    tareas_por_estado = {row["estado"]: row["total"] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    top = cursor.fetchone()
    proyecto_con_mas_tareas = dict(top) if top else None

    conn.close()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }