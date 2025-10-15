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


@app.get("/tareas")  # GET
def obtener_tareas(estado: str = None, texto: str = None):
    resultado = tareas_db

    # Filtro por estado
    if estado:
        # Cambié el status_code a 422 para mantener coherencia con las otras validaciones
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t["estado"] == estado]

    # Filtro por texto
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]

    return resultado


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
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}

    for tarea in tareas_db:
        tarea["estado"] = "completada"

    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}


@app.put("/tareas/{id}")
def modificar_tarea(id: int, datos: dict = Body(...)):
    for tarea in tareas_db:
        if tarea["id"] == id:
            if "descripcion" in datos:
                if not datos["descripcion"].strip():
                    raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})
                tarea["descripcion"] = datos["descripcion"].strip()

            if "estado" in datos:
                if datos["estado"] not in ESTADOS_VALIDOS:
                    raise HTTPException(status_code=422, detail={"error": "Estado inválido"})
                tarea["estado"] = datos["estado"]

            return tarea

    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for i, tarea in enumerate(tareas_db):
        if tarea["id"] == id:
            del tareas_db[i]
            return {"mensaje": "Tarea eliminada exitosamente"}

    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
    return resumen



