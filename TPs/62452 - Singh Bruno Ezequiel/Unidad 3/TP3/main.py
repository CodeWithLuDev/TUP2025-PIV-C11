from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sqlite3

DB_NAME = "tareas.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT DEFAULT 'media'
        )
    """)
    conn.commit()
    conn.close()

# Ejecutamos la inicialización al arrancar el servidor
init_db()


app = FastAPI()

# Lista de tareas en memoria
tareas_db = []

# Estados válidos
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]
contador_id = 1


class Tarea(BaseModel):
    descripcion: str
    estado: str = "pendiente"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root():
    return """
    <html>
        <head>
            <title>Agenda de Contactos API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #1e90ff, #00bfff);
                    color: white;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    text-align: center;
                }
                h1 {
                    font-size: 2.5em;
                    margin-bottom: 0.3em;
                }
                p {
                    font-size: 1.2em;
                    margin-bottom: 1.5em;
                }
                a {
                    background-color: white;
                    color: #1e90ff;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    transition: background 0.3s, color 0.3s;
                }
                a:hover {
                    background-color: #1e90ff;
                    color: white;
                }
            </style>
        </head>
        <body>
            <h1>📒 Bienvenido a la Agenda de Contactos API</h1>
            <p>Tu servidor FastAPI está funcionando correctamente.</p>
            <a href="/docs">Ver Documentación Interactiva</a>
        </body>
    </html>
    """


@app.get("/tareas")
def obtener_tareas(estado: str = None, texto: str = None, prioridad: str = None, orden: str = "asc"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Base de la consulta
    query = "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE 1=1"
    params = []

    # Filtro por estado
    if estado:
        if estado not in ESTADOS_VALIDOS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})
        query += " AND estado = ?"
        params.append(estado)

    # Filtro por texto
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")

    # Filtro por prioridad
    if prioridad:
        if prioridad not in ["baja", "media", "alta"]:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Prioridad inválida"})
        query += " AND prioridad = ?"
        params.append(prioridad)

    # Orden
    if orden.lower() not in ["asc", "desc"]:
        orden = "asc"

    query += f" ORDER BY fecha_creacion {orden.upper()}"

    # Ejecutamos la consulta
    cursor.execute(query, params)
    filas = cursor.fetchall()
    conn.close()

    # Convertimos los resultados en JSON
    tareas = [
        {
            "id": fila[0],
            "descripcion": fila[1],
            "estado": fila[2],
            "fecha_creacion": fila[3],
            "prioridad": fila[4],
        }
        for fila in filas
    ]

    return tareas


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    descripcion = tarea.descripcion.strip()
    estado = tarea.estado

    if not descripcion:
        raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})

    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=422, detail={"error": "Estado inválido"})

    fecha_creacion = datetime.now().isoformat()
    prioridad = "media"  # valor por defecto

    # Insertamos en la base de datos
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (descripcion, estado, fecha_creacion, prioridad))
    conn.commit()

    # Recuperamos la tarea recién creada para devolverla
    nueva_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (nueva_id,))
    fila = cursor.fetchone()
    conn.close()

    return {
        "id": fila[0],
        "descripcion": fila[1],
        "estado": fila[2],
        "fecha_creacion": fila[3],
        "prioridad": fila[4]
    }

@app.put("/tareas/completar_todas", status_code=200)
def completar_todas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ¿Hay tareas en la tabla?
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cursor.fetchone()[0]
    if total_tareas == 0:
        conn.close()
        return {"mensaje": "No hay tareas para completar"}

    # Actualizamos sólo las que no estén ya en 'completada'
    cursor.execute("UPDATE tareas SET estado = ? WHERE estado != ?", ("completada", "completada"))
    conn.commit()

    # rowcount indica cuántas filas fueron afectadas
    actualizadas = cursor.rowcount if cursor.rowcount is not None else 0

    conn.close()

    if actualizadas == 0:
        return {"mensaje": "Todas las tareas ya están completadas", "actualizadas": 0}
    else:
        return {"mensaje": "Tareas marcadas como completadas", "actualizadas": actualizadas}


@app.put("/tareas/{id}")
def modificar_tarea(id: int, datos: dict = Body(...)):
    campos_validos = ["descripcion", "estado", "prioridad"]

    if not any(campo in datos for campo in campos_validos):
        raise HTTPException(status_code=422, detail={"error": "No se proporcionaron campos válidos para actualizar"})

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verificamos que la tarea exista
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

    # Validaciones
    if "descripcion" in datos:
        if not datos["descripcion"].strip():
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})

    if "estado" in datos:
        if datos["estado"] not in ESTADOS_VALIDOS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})

    if "prioridad" in datos:
        if datos["prioridad"] not in ["baja", "media", "alta"]:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Prioridad inválida"})

    # Construimos la consulta dinámica
    campos = []
    valores = []
    for campo in campos_validos:
        if campo in datos:
            campos.append(f"{campo} = ?")
            valores.append(datos[campo].strip() if campo == "descripcion" else datos[campo])

    valores.append(id)
    query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"

    cursor.execute(query, valores)
    conn.commit()

    # Devolvemos la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()

    return {
        "id": tarea_actualizada[0],
        "descripcion": tarea_actualizada[1],
        "estado": tarea_actualizada[2],
        "fecha_creacion": tarea_actualizada[3],
        "prioridad": tarea_actualizada[4]
    }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

    # Eliminar la tarea
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": f"Tarea con id {id} eliminada exitosamente"}


@app.get("/tareas/resumen")
def resumen_tareas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Contamos cuántas tareas hay por cada estado
    cursor.execute("""
        SELECT estado, COUNT(*) 
        FROM tareas 
        GROUP BY estado
    """)
    filas = cursor.fetchall()
    conn.close()

    # Inicializamos el resumen con 0 en todos los estados válidos
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}

    for estado, cantidad in filas:
        if estado in resumen:
            resumen[estado] = cantidad

    return resumen



