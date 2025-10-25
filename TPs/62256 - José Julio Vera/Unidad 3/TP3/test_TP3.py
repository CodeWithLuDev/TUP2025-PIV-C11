# test_TP3.py
import pytest
import httpx
import os
import time
from typing import Dict, Any, List

# URL base de tu aplicación FastAPI
BASE_URL = "http://127.0.0.1:8000"

# Cliente HTTP para las peticiones
client = httpx.Client(base_url=BASE_URL)

# ------------------------------------------------------------------------------
# Fixtures y Setup Global
# ------------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Fixture para asegurar que la API esté viva y limpiar la DB antes y después."""
    try:
        # 1. Verificar conexión y limpiar DB antes de empezar
        client.delete("/limpiar_db")
        print("\n--- DB Limpiada al inicio ---")
    except httpx.ConnectError:
        pytest.fail(f"No se pudo conectar a FastAPI en {BASE_URL}. Asegúrate de que uvicorn main:app --reload esté corriendo.")
    
    yield
    
    # 2. Limpiar al finalizar
    client.delete("/limpiar_db")
    print("--- DB Limpiada al finalizar ---")

@pytest.fixture(scope="function")
def setup_tareas_para_filtros():
    """Fixture para crear un set de tareas para el filtrado, incluyendo prioridad."""
    client.delete("/limpiar_db")
    
    # Tarea 1: Python, pendiente, baja
    client.post("/tareas", json={"descripcion": "Estudiar Python", "estado": "pendiente", "prioridad": "baja"})
    time.sleep(0.01) # Pequeña pausa para asegurar diferencia de fecha_creacion
    # Tarea 2: FastAPI, en_progreso, media
    client.post("/tareas", json={"descripcion": "Estudiar FastAPI", "estado": "en_progreso", "prioridad": "media"})
    time.sleep(0.01)
    # Tarea 3: TP1, completada, alta
    client.post("/tareas", json={"descripcion": "Completar TP1", "estado": "completada", "prioridad": "alta"})
    time.sleep(0.01)
    # Tarea 4: Teclado, pendiente, media
    client.post("/tareas", json={"descripcion": "Comprar teclado Mecanico", "estado": "pendiente", "prioridad": "media"})
    time.sleep(0.01)
    # Tarea 5: Proyecto, completada, alta
    client.post("/tareas", json={"descripcion": "Finalizar Proyecto", "estado": "completada", "prioridad": "alta"})
    
    # Se espera que los IDs sean 1, 2, 3, 4, 5
    
# ------------------------------------------------------------------------------
# TESTS DE CRUD PERSISTENTE (1-9)
# ------------------------------------------------------------------------------

def test_01_obtener_tareas_vacia():
    """GET /tareas - Debe devolver una lista vacía al inicio."""
    client.delete("/limpiar_db")
    response = client.get("/tareas")
    assert response.status_code == 200
    assert response.json() == []

def test_02_crear_tarea_exitosamente():
    """POST /tareas - Creación exitosa (id 1)."""
    tarea_data = {"descripcion": "Comprar leche", "prioridad": "media"}
    response = client.post("/tareas", json=tarea_data)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["descripcion"] == "Comprar leche"
    assert data["estado"] == "pendiente" # Por defecto
    assert data["prioridad"] == "media"
    assert "fecha_creacion" in data

def test_03_crear_segunda_tarea_con_otro_estado_y_prioridad():
    """POST /tareas - Creación exitosa (id 2)."""
    tarea_data = {"descripcion": "Pagar cuentas", "estado": "en_progreso", "prioridad": "alta"}
    response = client.post("/tareas", json=tarea_data)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 2
    assert data["estado"] == "en_progreso"
    assert data["prioridad"] == "alta"

def test_04_obtener_todas_las_tareas_despues_de_crear():
    """GET /tareas - Debe devolver 2 tareas."""
    response = client.get("/tareas")
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 2

def test_05_actualizar_tarea_existente():
    """PUT /tareas/{id} - Actualización exitosa (id 1)."""
    update_data = {"descripcion": "Comprar leche y pan", "estado": "completada", "prioridad": "baja"}
    response = client.put("/tareas/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["descripcion"] == "Comprar leche y pan"
    assert data["estado"] == "completada"
    assert data["prioridad"] == "baja"

def test_06_actualizar_tarea_no_existente():
    """PUT /tareas/{id} - Debe retornar 404."""
    update_data = {"descripcion": "Tarea inexistente", "estado": "pendiente", "prioridad": "alta"}
    response = client.put("/tareas/999", json=update_data)
    assert response.status_code == 404
    assert "Tarea con id 999 no encontrada" in response.json().get("detail", {}).get("error", "")

def test_07_eliminar_tarea_existente():
    """DELETE /tareas/{id} - Eliminación exitosa (id 2)."""
    response = client.delete("/tareas/2")
    assert response.status_code == 200 
    assert response.json()["message"].startswith("Tarea con id 2 eliminada")

def test_08_verificar_eliminacion():
    """GET /tareas - Debe quedar solo 1 tarea (id 1)."""
    response = client.get("/tareas")
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1

def test_09_eliminar_tarea_no_existente():
    """DELETE /tareas/{id} - Debe retornar 404."""
    response = client.delete("/tareas/2") # Intentar eliminar la tarea ya eliminada (id 2)
    assert response.status_code == 404
    assert "Tarea con id 2 no encontrada" in response.json().get("detail", {}).get("error", "")

# ------------------------------------------------------------------------------
# TESTS DE VALIDACIÓN (10-12)
# ------------------------------------------------------------------------------

def test_10_crear_tarea_descripcion_vacia():
    """POST /tareas - Debe retornar 422 (Pydantic) por descripción vacía."""
    tarea_data = {"descripcion": "", "estado": "pendiente"}
    response = client.post("/tareas", json=tarea_data)
    assert response.status_code == 422

def test_11_crear_tarea_estado_invalido():
    """POST /tareas - Debe retornar 422 por estado inválido."""
    tarea_data = {"descripcion": "Leer un libro", "estado": "invalido", "prioridad": "media"}
    response = client.post("/tareas", json=tarea_data)
    assert response.status_code == 422

def test_12_actualizar_con_prioridad_invalida():
    """PUT /tareas/{id} - Debe retornar 422 por prioridad inválida en la actualización."""
    client.delete("/limpiar_db")
    client.post("/tareas", json={"descripcion": "Test", "prioridad": "media"}) # id 1
    update_data = {"descripcion": "Test", "estado": "completada", "prioridad": "critica"}
    response = client.put("/tareas/1", json=update_data)
    assert response.status_code == 422

# ------------------------------------------------------------------------------
# TESTS DE FILTROS, ORDENAMIENTO Y RESUMEN (13-20)
# ------------------------------------------------------------------------------

def test_13_filtrar_por_estado_pendiente(setup_tareas_para_filtros):
    """GET /tareas?estado=pendiente - Debe devolver 2 tareas (id 1, 4)."""
    response = client.get("/tareas", params={"estado": "pendiente"})
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 2
    assert all(t["estado"] == "pendiente" for t in tareas)

def test_14_filtrar_por_prioridad_alta(setup_tareas_para_filtros):
    """GET /tareas?prioridad=alta - Debe devolver 2 tareas (id 3, 5)."""
    response = client.get("/tareas", params={"prioridad": "alta"})
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 2
    assert all(t["prioridad"] == "alta" for t in tareas)

def test_15_filtrar_por_texto_y_estado(setup_tareas_para_filtros):
    """GET /tareas?texto=proyecto&estado=completada - Debe devolver 1 tarea (id 5)."""
    response = client.get("/tareas", params={"texto": "Proyecto", "estado": "completada"})
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 1
    assert "Finalizar Proyecto" in tareas[0]["descripcion"]

def test_16_ordenar_por_fecha_descendente(setup_tareas_para_filtros):
    """GET /tareas?orden=desc - Debe devolver las tareas de 5 a 1."""
    response = client.get("/tareas", params={"orden": "desc"})
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 5
    # Espera el orden de creación inverso: 5, 4, 3, 2, 1
    assert [t['id'] for t in tareas] == [5, 4, 3, 2, 1] 

def test_17_ordenar_por_fecha_ascendente(setup_tareas_para_filtros):
    """GET /tareas?orden=asc - Debe devolver las tareas de 1 a 5."""
    response = client.get("/tareas", params={"orden": "asc"})
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 5
    # Espera el orden de creación: 1, 2, 3, 4, 5
    assert [t['id'] for t in tareas] == [1, 2, 3, 4, 5]

def test_18_combinacion_de_filtros_y_orden(setup_tareas_para_filtros):
    """GET /tareas?estado=pendiente&prioridad=media&orden=asc - Debe devolver 1 tarea (id 4)."""
    params = {"estado": "pendiente", "prioridad": "media", "orden": "asc"}
    response = client.get("/tareas", params=params)
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 1
    assert tareas[0]["id"] == 4

def test_19_obtener_resumen_tareas(setup_tareas_para_filtros):
    """GET /tareas/resumen - Debe devolver el conteo correcto (2, 1, 2)."""
    response = client.get("/tareas/resumen")
    assert response.status_code == 200
    resumen = response.json()
    assert resumen == {
        "pendiente": 2,
        "en_progreso": 1,
        "completada": 2
    }
    
# ------------------------------------------------------------------------------
# TEST DE PERSISTENCIA (20)
# ------------------------------------------------------------------------------


def test_20_verificar_persistencia():
    """Verifica que los datos no se pierdan tras simular un "reinicio" de la DB."""
    client.delete("/limpiar_db")
    
    # 1. Crear una tarea (ID 1)
    client.post("/tareas", json={"descripcion": "Tarea Persistente", "prioridad": "alta"})
    
    # 2. Verificar que existe
    response_1 = client.get("/tareas")
    assert len(response_1.json()) == 1
    assert response_1.json()[0]["descripcion"] == "Tarea Persistente"
    
 
    client.post("/tareas", json={"descripcion": "Tarea 2", "prioridad": "baja"}) # ID 2
    client.post("/tareas", json={"descripcion": "Tarea 3", "prioridad": "baja"}) # ID 3
    
    response_final = client.get("/tareas")
    assert len(response_final.json()) == 3
    assert response_final.json()[-1]["id"] == 3