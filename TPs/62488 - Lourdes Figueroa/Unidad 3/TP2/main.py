from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal 
from datetime import datetime  

app= FastAPI(title="Mini API de Tareas", version="1.0.0")

# modelos pydantic
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion_no_vacia(cls,v):
        if not v or not v.strip():
            raise ValueError('La descripcion no puede estar vacia')
        return v.strip()
    
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None 
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] =None 

    
class Tarea(BaseModel):
    id: int
    descripcion: str 
    estado: Literal["pendiente", "en_progreso", "completada"]
    fecha_creacion: str

#base de datos en memoria
tareas_db = []
contador_id = 1

#rutas

@app.get("/")
def root():
    return {"mensaje": "Mini API de Tareas - TP2"}

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query (None, description="Filtrar por estado"),
    texto: Optional[str] = Query(None, description="Buscar por texto en descripcion")
):
    resultado = tareas_db.copy()
    
    
    if estado:
        if estado not in ["pendiente", "en_progreso", "completada"]:
            raise HTTPException(status_code=400, detail={"error": f"Estado '{estado}' no valido. Debe ser: pendiente, en_progreso o completada"})
        resultado = [t for t in resultado if t["estado"] == estado]
   
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado 


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    global contador_id
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    
    tareas_db.append(nueva_tarea)
    contador_id += 1
    
    return nueva_tarea

@app.get("/tareas/resumen")
def obtener_resumen():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
        
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    if not tareas_db:
        return{
            "mensaje": "No hay tareas para completar",
            "tareas_actualizadas": 0
        }
    
    tareas_actualizadas = 0
    
    for tarea in tareas_db:
        if tarea["estado"] != "completada":
            tarea["estado"] = "completada"
            tareas_actualizadas += 1
    
    return {
        "mensaje": f"Se completaron {tareas_actualizadas} tareas",
        "tareas_actualizadas": tareas_actualizadas
    }    

@app.get("/tareas/{id}")
def obtener_tarea(id: int):
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    
    if not tarea:
        raise HTTPException(status_code=404, detail={"error":"La tarea no existe"})
                                                             
    return tarea 


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    tarea = next ((t for t in tareas_db if t["id"] == id), None)  
    
    if not tarea:
        raise HTTPException(status_code=404, detail={"error":"La tarea no existe"})   
    
    if tarea_update.descripcion is not None:
        desc_limpia = tarea_update.descripcion.strip()
        if not desc_limpia:
            raise HTTPException(status_code=400, detail={"error":"La descripcion no puede estar vacia"})
        tarea["descripcion"] = desc_limpia        
        
    if tarea_update.estado is not None:
        tarea["estado"] = tarea_update.estado 
        
    return tarea 


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    global tareas_db
    
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    
    if not tarea:
        raise HTTPException(status_code=404, detail={"error":"La tarea no existe"})
    
    tareas_db = [t for t in tareas_db if t["id"] != id]
    
    return {"mensaje": "Tarea eliminada exitosamente","tarea": tarea }
                                                         