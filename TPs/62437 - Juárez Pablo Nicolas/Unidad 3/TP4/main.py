from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import sqlite3
from datetime import datetime
from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse,
    ResumenProyecto, ResumenGeneral
)

app = FastAPI(title="API de Gestión de Proyectos y Tareas", version="1.0.0")

DB_NAME = "tareas.db"

def get_db():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Activar claves foráneas
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas si no existen"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Crear tabla proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    # Crear tabla tareas con clave foránea
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al iniciar la aplicación
@app.on_event("startup")
def startup_event():
    init_db()

# === ENDPOINTS DE PROYECTOS ===

@app.get("/proyectos", response_model=list[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)")):
    """Lista todos los proyectos con opción de filtrar por nombre"""
    conn = get_db()
    cursor = conn.cursor()
    
    if nombre:
        cursor.execute("SELECT * FROM proyectos WHERE nombre LIKE ?", (f"%{nombre}%",))
    else:
        cursor.execute("SELECT * FROM proyectos")
    
    proyectos = []
    for row in cursor.fetchall():
        proyecto = dict(row)
        # Contar tareas asociadas
        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto['id'],))
        total_tareas = cursor.fetchone()['total']
        proyecto['total_tareas'] = total_tareas
        proyectos.append(proyecto)
    
    conn.close()
    return proyectos

@app.get("/proyectos/{id}", response_model=ProyectoResponse)
def obtener_proyecto(id: int):
    """Obtiene un proyecto específico con el contador de tareas asociadas"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Proyecto con id {id} no encontrado")
    
    proyecto = dict(proyecto)
    # Contar tareas asociadas
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()['total']
    proyecto['total_tareas'] = total_tareas
    
    conn.close()
    return proyecto

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto"""
    conn = get_db()
    cursor = conn.cursor()
    fecha_creacion = datetime.now().isoformat()
    
    try:
        cursor.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (proyecto.nombre, proyecto.descripcion, fecha_creacion)
        )
        conn.commit()
        proyecto_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": proyecto_id,
            "nombre": proyecto.nombre,
            "descripcion": proyecto.descripcion,
            "fecha_creacion": fecha_creacion,
            "total_tareas": 0
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )

@app.put("/proyectos/{id}", response_model=ProyectoResponse)
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    """Modifica un proyecto existente"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si existe el proyecto
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Proyecto con id {id} no encontrado")
    
    # Construir query dinámicamente
    updates = []
    params = []
    
    if proyecto.nombre is not None:
        updates.append("nombre = ?")
        params.append(proyecto.nombre)
    if proyecto.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(proyecto.descripcion)
    
    if updates:
        params.append(id)
        query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
        
        try:
            cursor.execute(query, params)
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            raise HTTPException(
                status_code=409,
                detail="Error al actualizar el proyecto. Puede que el nombre ya exista"
            )
    
    # Devolver el proyecto actualizado
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto_actualizado = dict(cursor.fetchone())
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()['total']
    proyecto_actualizado['total_tareas'] = total_tareas
    
    conn.close()
    return proyecto_actualizado

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    """Elimina un proyecto y todas sus tareas asociadas (CASCADE)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que existe el proyecto
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Proyecto con id {id} no encontrado")
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    tareas_eliminadas = cursor.fetchone()['total']
    
    # Eliminar proyecto (CASCADE eliminará las tareas)
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Proyecto eliminado correctamente", "tareas_eliminadas": tareas_eliminadas}

# === ENDPOINTS DE TAREAS ===

@app.get("/proyectos/{id}/tareas", response_model=list[TareaResponse])
def listar_tareas_proyecto(
    id: int,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    orden: str = Query("asc", description="Orden por fecha (asc o desc)")
):
    """Lista todas las tareas de un proyecto específico"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Proyecto con id {id} no encontrado")
    
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [id]
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden.lower() == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

@app.get("/tareas", response_model=list[TareaResponse])
def listar_todas_tareas(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    orden: str = Query("asc", description="Orden por fecha (asc o desc)")
):
    """Lista todas las tareas con múltiples filtros opcionales"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if proyecto_id is not None:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden.lower() == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

@app.post("/proyectos/{id}/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    """Crea una nueva tarea dentro de un proyecto"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"No se puede crear la tarea. El proyecto con id {id} no existe"
        )
    
    fecha_creacion = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion)
    )
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "proyecto_id": id,
        "fecha_creacion": fecha_creacion
    }

@app.put("/tareas/{id}", response_model=TareaResponse)
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Modifica una tarea existente (puede cambiar de proyecto)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Tarea con id {id} no encontrada")
    
    # Si se intenta cambiar de proyecto, verificar que existe
    if tarea.proyecto_id is not None:
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (tarea.proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"No se puede mover la tarea. El proyecto con id {tarea.proyecto_id} no existe"
            )
    
    # Construir query dinámicamente
    updates = []
    params = []
    
    if tarea.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(tarea.descripcion)
    if tarea.estado is not None:
        updates.append("estado = ?")
        params.append(tarea.estado)
    if tarea.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(tarea.prioridad)
    if tarea.proyecto_id is not None:
        updates.append("proyecto_id = ?")
        params.append(tarea.proyecto_id)
    
    if updates:
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Devolver la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = dict(cursor.fetchone())
    conn.close()
    return tarea_actualizada

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Tarea con id {id} no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente"}

# === ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ===

@app.get("/proyectos/{id}/resumen", response_model=ResumenProyecto)
def obtener_resumen_proyecto(id: int):
    """Devuelve estadísticas detalladas de un proyecto"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Proyecto con id {id} no encontrado")
    
    # Contar tareas totales
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()['total']
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ? 
        GROUP BY estado
    """, (id,))
    por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ? 
        GROUP BY prioridad
    """, (id,))
    por_prioridad = {row['prioridad']: row['cantidad'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto['nombre'],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen", response_model=ResumenGeneral)
def obtener_resumen_general():
    """Devuelve un resumen general de toda la aplicación"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total de proyectos
    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()['total']
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()['total']
    
    # Tareas por estado
    cursor.execute("SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado")
    tareas_por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
    
    # Proyecto con más tareas
    cursor.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    proyecto_top = cursor.fetchone()
    
    proyecto_con_mas_tareas = None
    if proyecto_top and proyecto_top['cantidad_tareas'] > 0:
        proyecto_con_mas_tareas = {
            "id": proyecto_top['id'],
            "nombre": proyecto_top['nombre'],
            "cantidad_tareas": proyecto_top['cantidad_tareas']
        }
    
    conn.close()
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }

# Endpoint raíz
@app.get("/")
def root():
    return {
        "mensaje": "API de Gestión de Proyectos y Tareas",
        "version": "1.0.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "resumen": "/resumen",
            "documentacion": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)