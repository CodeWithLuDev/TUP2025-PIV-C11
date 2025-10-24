from fastapi import FastAPI, HTTPException
from datetime import datetime
import sqlite3

from database import init_db
from models import ProyectoCreate

app = FastAPI()
init_db()


#Post Proyectos

@app.post("/proyectos")
def crear_proyecto(proyecto: ProyectoCreate):
    if not proyecto.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del proyecto no puede estar vacío")

    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Verificar si ya existe un proyecto con ese nombre
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")

    fecha_actual = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    """, (proyecto.nombre, proyecto.descripcion, fecha_actual))

    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()

    return {
        "id": nuevo_id,
        "nombre": proyecto.nombre,
        "descripcion": proyecto.descripcion,
        "fecha_creacion": fecha_actual
    }

#Get Proyectos

@app.get("/proyectos")
def listar_proyectos():
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Traer todos los proyectos
    cursor.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos")
    proyectos = cursor.fetchall()

    resultado = []

    for proyecto in proyectos:
        proyecto_id = proyecto[0]
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        cantidad_tareas = cursor.fetchone()[0]

        resultado.append({
            "id": proyecto_id,
            "nombre": proyecto[1],
            "descripcion": proyecto[2],
            "fecha_creacion": proyecto[3],
            "cantidad_tareas": cantidad_tareas
        })

    conn.close()
    return resultado


#Pos TareasCreate

from models import TareaCreate

@app.post("/proyectos/{id}/tareas")
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Verificar que el proyecto exista
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="El proyecto no existe")

    fecha_actual = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_actual))

    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()

    return {
        "id": nuevo_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "proyecto_id": id,
        "fecha_creacion": fecha_actual
    }


#Get Proyecto Tareas
@app.get("/proyectos/{id}/tareas")
def listar_tareas_de_proyecto(id: int):
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Verificar que el proyecto exista
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="El proyecto no existe")

    # Traer todas las tareas del proyecto
    cursor.execute("""
        SELECT id, descripcion, estado, prioridad, fecha_creacion
        FROM tareas
        WHERE proyecto_id = ?
    """, (id,))
    tareas = cursor.fetchall()
    conn.close()

    resultado = []
    for tarea in tareas:
        resultado.append({
            "id": tarea[0],
            "descripcion": tarea[1],
            "estado": tarea[2],
            "prioridad": tarea[3],
            "fecha_creacion": tarea[4]
        })

    return resultado


# GET /tareas - Listar todas las tareas con filtros por estado, prioridad, proyecto y orden
from fastapi import Query
from typing import Optional, Literal

@app.get("/tareas")
def listar_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query("asc")
):
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Construir la consulta dinámica
    consulta = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE 1=1"
    parametros = []

    if estado:
        consulta += " AND estado = ?"
        parametros.append(estado)

    if prioridad:
        consulta += " AND prioridad = ?"
        parametros.append(prioridad)

    if proyecto_id:
        consulta += " AND proyecto_id = ?"
        parametros.append(proyecto_id)

    consulta += f" ORDER BY fecha_creacion {orden.upper()}"

    cursor.execute(consulta, tuple(parametros))
    tareas = cursor.fetchall()
    conn.close()

    resultado = []
    for tarea in tareas:
        resultado.append({
            "id": tarea[0],
            "descripcion": tarea[1],
            "estado": tarea[2],
            "prioridad": tarea[3],
            "proyecto_id": tarea[4],
            "fecha_creacion": tarea[5]
        })

    return resultado

# PUT /tareas/{id} - Modificar una tarea existente

@app.put("/tareas/{id}")
def modificar_tarea(id: int, tarea: TareaCreate):
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Verificar que la tarea exista
    cursor.execute("SELECT id FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="La tarea no existe")

    cursor.execute("""
        UPDATE tareas
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, id))

    conn.commit()
    conn.close()

    return {
        "id": id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "mensaje": "Tarea actualizada correctamente"
    }


# DELETE /tareas/{id} - Eliminar una tarea por ID

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Verificar que la tarea exista
    cursor.execute("SELECT id FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="La tarea no existe")

    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": f"Tarea con ID {id} eliminada correctamente"}

# GET /resumen - Estadísticas generales de tareas por estado y prioridad

@app.get("/resumen")
def resumen_general():
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Conteo por estado
    cursor.execute("""
        SELECT estado, COUNT(*) FROM tareas GROUP BY estado
    """)
    estado_data = cursor.fetchall()
    resumen_estado = {estado: cantidad for estado, cantidad in estado_data}

    # Conteo por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad
    """)
    prioridad_data = cursor.fetchall()
    resumen_prioridad = {prioridad: cantidad for prioridad, cantidad in prioridad_data}

    conn.close()

    return {
        "resumen_estado": resumen_estado,
        "resumen_prioridad": resumen_prioridad
    }

# GET /proyectos/{id}/resumen - Estadísticas de tareas por estado y prioridad para un proyecto

@app.get("/proyectos/{id}/resumen")
def resumen_por_proyecto(id: int):
    conn = sqlite3.connect("tareas.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Verificar que el proyecto exista
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="El proyecto no existe")

    # Conteo por estado
    cursor.execute("""
        SELECT estado, COUNT(*) FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (id,))
    estado_data = cursor.fetchall()
    resumen_estado = {estado: cantidad for estado, cantidad in estado_data}

    # Conteo por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (id,))
    prioridad_data = cursor.fetchall()
    resumen_prioridad = {prioridad: cantidad for prioridad, cantidad in prioridad_data}

    conn.close()

    return {
        "proyecto_id": id,
        "resumen_estado": resumen_estado,
        "resumen_prioridad": resumen_prioridad
    }
