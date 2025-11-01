from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import sqlite3

from models import (
    ProyectoCreate, 
    ProyectoResponse, 
    ProyectoConTareas,
    TareaCreate, 
    TareaUpdate, 
    TareaResponse
)
from database import (
    init_db,
    obtener_conexion,
    DB_NAME
)


app = FastAPI(title="API de Proyectos y Tareas", version="1.0.0")

init_db()

@app.post("/proyectos", status_code=201, response_model=ProyectoResponse)
async def crear_proyecto(datos_proyecto: ProyectoCreate):
    """Crear un nuevo proyecto"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    try:
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (datos_proyecto.nombre, datos_proyecto.descripcion, timestamp))
        
        db.commit()
        nuevo_id = cursor.lastrowid
        db.close()
        
        return {
            "id": nuevo_id,
            "nombre": datos_proyecto.nombre,
            "descripcion": datos_proyecto.descripcion,
            "fecha_creacion": timestamp
        }
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un proyecto con ese nombre"
        )


@app.get("/proyectos", response_model=List[ProyectoResponse])
async def obtener_proyectos(nombre: Optional[str] = Query(None)):
    """Listar todos los proyectos con filtro opcional por nombre"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    if nombre:
        cursor.execute("""
            SELECT * FROM proyectos 
            WHERE nombre LIKE ?
            ORDER BY fecha_creacion DESC
        """, (f"%{nombre}%",))
    else:
        cursor.execute("SELECT * FROM proyectos ORDER BY fecha_creacion DESC")
    
    lista_proyectos = cursor.fetchall()
    db.close()
    
    return [dict(proyecto) for proyecto in lista_proyectos]


@app.get("/proyectos/{proyecto_id}", response_model=ProyectoConTareas)
async def obtener_proyecto_por_id(proyecto_id: int):
    """Obtener un proyecto específico con contador de tareas"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto_encontrado = cursor.fetchone()
    
    if not proyecto_encontrado:
        db.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    cantidad_tareas = cursor.fetchone()[0]
    
    db.close()
    
    return {
        **dict(proyecto_encontrado),
        "total_tareas": cantidad_tareas
    }


@app.put("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
async def modificar_proyecto(proyecto_id: int, datos_proyecto: ProyectoCreate):
    """Actualizar un proyecto existente"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto_actual = cursor.fetchone()
    
    if not proyecto_actual:
        db.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    try:
        cursor.execute("""
            UPDATE proyectos 
            SET nombre = ?, descripcion = ?
            WHERE id = ?
        """, (datos_proyecto.nombre, datos_proyecto.descripcion, proyecto_id))
        
        db.commit()
        db.close()
        
        return {
            "id": proyecto_id,
            "nombre": datos_proyecto.nombre,
            "descripcion": datos_proyecto.descripcion,
            "fecha_creacion": proyecto_actual['fecha_creacion']
        }
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un proyecto con ese nombre"
        )


@app.delete("/proyectos/{proyecto_id}")
async def borrar_proyecto(proyecto_id: int):
    """Eliminar un proyecto y sus tareas (CASCADE)"""
    db = obtener_conexion()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    cantidad_tareas_eliminadas = cursor.fetchone()[0]
    
    # Eliminar proyecto (CASCADE eliminará las tareas)
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    db.commit()
    db.close()
    
    return {
        "mensaje": f"Proyecto {proyecto_id} eliminado correctamente",
        "tareas_eliminadas": cantidad_tareas_eliminadas
    }


@app.post("/proyectos/{proyecto_id}/tareas", status_code=201, response_model=TareaResponse)
async def agregar_tarea(proyecto_id: int, datos_tarea: TareaCreate):
    """Crear una tarea dentro de un proyecto"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(
            status_code=400,
            detail="El proyecto especificado no existe"
        )
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (datos_tarea.descripcion, datos_tarea.estado, datos_tarea.prioridad, proyecto_id, timestamp))
    
    db.commit()
    id_nueva_tarea = cursor.lastrowid
    db.close()
    
    return {
        "id": id_nueva_tarea,
        "descripcion": datos_tarea.descripcion,
        "estado": datos_tarea.estado,
        "prioridad": datos_tarea.prioridad,
        "proyecto_id": proyecto_id,
        "fecha_creacion": timestamp
    }


@app.get("/proyectos/{proyecto_id}/tareas", response_model=List[TareaResponse])
async def obtener_tareas_de_proyecto(proyecto_id: int):
    """Listar todas las tareas de un proyecto específico"""
    db = obtener_conexion()
    cursor = db.cursor()
    

    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    

    cursor.execute("""
        SELECT * FROM tareas 
        WHERE proyecto_id = ?
        ORDER BY fecha_creacion ASC
    """, (proyecto_id,))
    
    lista_tareas = cursor.fetchall()
    db.close()
    
    return [dict(tarea) for tarea in lista_tareas]


@app.get("/tareas", response_model=List[TareaResponse])
async def listar_tareas(
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[str] = Query("asc")
):
    """Listar todas las tareas con filtros opcionales"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    consulta = "SELECT * FROM tareas WHERE 1=1"
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
    
    if orden == "desc":
        consulta += " ORDER BY fecha_creacion DESC"
    else:
        consulta += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(consulta, parametros)
    todas_tareas = cursor.fetchall()
    db.close()
    
    return [dict(tarea) for tarea in todas_tareas]


@app.put("/tareas/{tarea_id}", response_model=TareaResponse)
async def modificar_tarea(tarea_id: int, datos_actualizacion: TareaUpdate):
    """Actualizar una tarea existente"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_actual = cursor.fetchone()
    
    if not tarea_actual:
        db.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if datos_actualizacion.proyecto_id is not None:
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (datos_actualizacion.proyecto_id,))
        if not cursor.fetchone():
            db.close()
            raise HTTPException(
                status_code=400,
                detail="El proyecto especificado no existe"
            )

    nueva_descripcion = datos_actualizacion.descripcion if datos_actualizacion.descripcion is not None else tarea_actual['descripcion']
    nuevo_estado = datos_actualizacion.estado if datos_actualizacion.estado is not None else tarea_actual['estado']
    nueva_prioridad = datos_actualizacion.prioridad if datos_actualizacion.prioridad is not None else tarea_actual['prioridad']
    nuevo_proyecto = datos_actualizacion.proyecto_id if datos_actualizacion.proyecto_id is not None else tarea_actual['proyecto_id']
    
    cursor.execute("""
        UPDATE tareas 
        SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ?
        WHERE id = ?
    """, (nueva_descripcion, nuevo_estado, nueva_prioridad, nuevo_proyecto, tarea_id))
    
    db.commit()
    db.close()
    
    return {
        "id": tarea_id,
        "descripcion": nueva_descripcion,
        "estado": nuevo_estado,
        "prioridad": nueva_prioridad,
        "proyecto_id": nuevo_proyecto,
        "fecha_creacion": tarea_actual['fecha_creacion']
    }


@app.delete("/tareas/{tarea_id}")
async def borrar_tarea(tarea_id: int):
    """Eliminar una tarea específica"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        db.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    db.commit()
    db.close()
    
    return {"mensaje": f"Tarea {tarea_id} eliminada correctamente"}



@app.get("/proyectos/{proyecto_id}/resumen")
async def obtener_resumen_proyecto(proyecto_id: int):
    """Obtener resumen estadístico de un proyecto"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto_info = cursor.fetchone()
    
    if not proyecto_info:
        db.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT estado, COUNT(*) 
        FROM tareas 
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (proyecto_id,))
    conteo_estados = {fila[0]: fila[1] for fila in cursor.fetchall()}
    
    cursor.execute("""
        SELECT prioridad, COUNT(*) 
        FROM tareas 
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (proyecto_id,))
    conteo_prioridades = {fila[0]: fila[1] for fila in cursor.fetchall()}
    
    db.close()
    
    todos_estados = ["pendiente", "en_progreso", "completada"]
    todas_prioridades = ["baja", "media", "alta"]
    
    for est in todos_estados:
        if est not in conteo_estados:
            conteo_estados[est] = 0
    
    for pri in todas_prioridades:
        if pri not in conteo_prioridades:
            conteo_prioridades[pri] = 0
    
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto_info['nombre'],
        "total_tareas": total,
        "por_estado": conteo_estados,
        "por_prioridad": conteo_prioridades
    }


@app.get("/resumen")
async def obtener_resumen_completo():
    """Obtener resumen general de toda la aplicación"""
    db = obtener_conexion()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    cant_proyectos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    cant_tareas = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT estado, COUNT(*) 
        FROM tareas 
        GROUP BY estado
    """)
    distribucion_estados = {fila[0]: fila[1] for fila in cursor.fetchall()}
    
    todos_estados = ["pendiente", "en_progreso", "completada"]
    for est in todos_estados:
        if est not in distribucion_estados:
            distribucion_estados[est] = 0
    
    proyecto_top = None
    if cant_proyectos > 0:
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as num_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY num_tareas DESC
            LIMIT 1
        """)
        resultado_top = cursor.fetchone()
        if resultado_top:
            proyecto_top = {
                "id": resultado_top[0],
                "nombre": resultado_top[1],
                "cantidad_tareas": resultado_top[2]
            }
    
    db.close()
    
    return {
        "total_proyectos": cant_proyectos,
        "total_tareas": cant_tareas,
        "tareas_por_estado": distribucion_estados,
        "proyecto_con_mas_tareas": proyecto_top
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)