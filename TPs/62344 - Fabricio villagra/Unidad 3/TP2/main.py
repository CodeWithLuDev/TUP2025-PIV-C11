from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Inicializar la aplicación FastAPI
app = FastAPI()

# Modelo Pydantic para validación de tareas
class Task(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: Optional[datetime] = None

# Almacenamiento de tareas en memoria con tareas iniciales
tasks = [
    {"id": 1, "descripcion": "Enviar correo a Fabricio Villagra", "estado": "pendiente", "fecha_creacion": datetime.now()},
    {"id": 2, "descripcion": "Llamar a Ulises Urquiza para reunión", "estado": "en_progreso", "fecha_creacion": datetime.now()},
    {"id": 3, "descripcion": "Revisar documento de Nacho Kermes", "estado": "completada", "fecha_creacion": datetime.now()},
    {"id": 4, "descripcion": "Coordinar con Lucas Umaño", "estado": "pendiente", "fecha_creacion": datetime.now()},
    {"id": 5, "descripcion": "Actualizar contacto de Lucas Albornoz", "estado": "en_progreso", "fecha_creacion": datetime.now()},
    {"id": 6, "descripcion": "Enviar mensaje a Martín Herrera", "estado": "completada", "fecha_creacion": datetime.now()},
    {"id": 7, "descripcion": "Confirmar cita con Luis Vera", "estado": "pendiente", "fecha_creacion": datetime.now()},
    {"id": 8, "descripcion": "Reunión con Fabricio Bulovich", "estado": "en_progreso", "fecha_creacion": datetime.now()},
    {"id": 9, "descripcion": "Preparar informe para Ramiro Karake", "estado": "completada", "fecha_creacion": datetime.now()},
    {"id": 10, "descripcion": "Contactar a Juan Pichon por proyecto", "estado": "pendiente", "fecha_creacion": datetime.now()}
]

# Estados válidos para las tareas
VALID_STATES = {"pendiente", "en_progreso", "completada"}

# Endpoint GET raíz
@app.get("/")
def welcome():
    return {"mensaje": "Bienvenido a la Mini API de Tareas"}

# Endpoint GET para obtener todas las tareas
@app.get("/tareas", response_model=List[Task])
def get_tasks():
    return tasks

# Endpoint GET para filtrar tareas por estado o texto
@app.get("/tareas/", response_model=List[Task])
def filter_tasks(estado: Optional[str] = None, texto: Optional[str] = None):
    filtered_tasks = tasks
    if estado:
        # Validar estado proporcionado
        if estado not in VALID_STATES:
            raise HTTPException(status_code=400, detail="Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'.")
        filtered_tasks = [task for task in filtered_tasks if task["estado"] == estado]
    if texto:
        # Filtrar por texto en la descripción
        filtered_tasks = [task for task in filtered_tasks if texto.lower() in task["descripcion"].lower()]
    return filtered_tasks

# Endpoint GET para obtener resumen de tareas por estado
@app.get("/tareas/resumen")
def get_task_summary():
    # Contar tareas por estado
    summary = {
        "pendiente": sum(1 for task in tasks if task["estado"] == "pendiente"),
        "en_progreso": sum(1 for task in tasks if task["estado"] == "en_progreso"),
        "completada": sum(1 for task in tasks if task["estado"] == "completada")
    }
    return summary

# Endpoint POST para crear una nueva tarea
@app.post("/tareas", response_model=Task)
def create_task(task: Task):
    # Validar descripción no vacía
    if not task.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía.")
    # Validar estado
    if task.estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail="Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'.")
    
    # Verificar si el ID ya existe
    if any(t["id"] == task.id for t in tasks):
        raise HTTPException(status_code=400, detail="El ID de la tarea ya existe.")
    
    # Agregar fecha de creación
    task_data = task.dict()
    task_data["fecha_creacion"] = datetime.now()
    
    tasks.append(task_data)
    return task_data

# Endpoint PUT para actualizar una tarea por ID
@app.put("/tareas/{id}", response_model=Task)
def update_task(id: int, updated_task: Task):
    # Validar descripción no vacía
    if updated_task.descripcion.strip() == "":
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía.")
    # Validar estado
    if updated_task.estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail="Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'.")
    
    # Buscar y actualizar tarea
    for index, task in enumerate(tasks):
        if task["id"] == id:
            tasks[index] = updated_task.dict()
            tasks[index]["fecha_creacion"] = task["fecha_creacion"]  # Preservar fecha de creación original
            return tasks[index]
    
    # Lanzar error si la tarea no existe
    raise HTTPException(status_code=404, detail="La tarea no existe.")

# Endpoint DELETE para eliminar una tarea por ID
@app.delete("/tareas/{id}")
def delete_task(id: int):
    # Buscar y eliminar tarea
    for index, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(index)
            return {"mensaje": f"Tarea con ID {id} eliminada correctamente."}
    
    # Lanzar error si la tarea no existe
    raise HTTPException(status_code=404, detail="La tarea no existe.")

# Endpoint PUT para marcar todas las tareas como completadas
@app.put("/tareas/completar_todas")
def complete_all_tasks():
    # Actualizar estado de todas las tareas a completada
    for task in tasks:
        task["estado"] = "completada"
    return {"mensaje": "Todas las tareas han sido marcadas como completadas."}



