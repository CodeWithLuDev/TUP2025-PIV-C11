from fastapi import FastAPI, HTTPException
from datetime import datetime
from fastapi.responses import HTMLResponse

app = FastAPI()

# Lista de tareas en memoria
tareas = []

# Estados válidos
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]
ID_COUNTER = 1




from fastapi.responses import HTMLResponse

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




@app.get("/tareas")                     #GET
def obtener_tareas(estado: str = None, texto: str = None):
    resultado = tareas

    # Filtro por estado
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail="Estado inválido")
        resultado = [t for t in resultado if t["estado"] == estado]

    # Filtro por texto
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]

    return resultado

@app.post("/tareas")                    #POST
def crear_tarea(tarea: dict):
    descripcion = tarea.get("descripcion", "").strip()
    estado = tarea.get("estado", "pendiente")

    if not descripcion:
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")

    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")

    nueva_tarea = {
        "id": len(tareas) + 1,
        "descripcion": descripcion,
        "estado": estado,
        "fecha_creacion": datetime.now().isoformat()
    }

    tareas.append(nueva_tarea)
    return nueva_tarea

@app.put("/tareas/{id}")            #PUT
def modificar_tarea(id: int, datos: dict):
    for tarea in tareas:
        if tarea["id"] == id:
            if "descripcion" in datos:
                if not datos["descripcion"].strip():
                    raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
                tarea["descripcion"] = datos["descripcion"]

            if "estado" in datos:
                if datos["estado"] not in ESTADOS_VALIDOS:
                    raise HTTPException(status_code=400, detail="Estado inválido")
                tarea["estado"] = datos["estado"]

            return tarea

    raise HTTPException(status_code=404, detail="La tarea no existe")


@app.delete("/tareas/{id}")             #DELETE
def eliminar_tarea(id: int):
    for i, tarea in enumerate(tareas):
        if tarea["id"] == id:
            tareas.pop(i)
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail="La tarea no existe")



@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for tarea in tareas:
        resumen[tarea["estado"]] += 1
    return resumen



@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}

    for tarea in tareas:
        tarea["estado"] = "completada"

    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
