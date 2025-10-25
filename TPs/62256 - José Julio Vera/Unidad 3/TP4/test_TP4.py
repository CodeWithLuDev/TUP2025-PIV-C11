# test_TP4.py
import pytest
import httpx
from typing import Dict, Any, List
import time

# URL base de tu aplicación FastAPI
BASE_URL = "http://127.0.0.1:8000"
client = httpx.Client(base_url=BASE_URL)

# ------------------------------------------------------------------------------
# Fixtures y Setup Global
# ------------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def setup_teardown_module():
    """Fixture para asegurar que la API esté viva y limpiar la DB antes y después."""
    try:
        # 1. Verificar conexión y limpiar DB antes de empezar
        client.delete("/limpiar_db")
        print("\n--- DB Limpiada al inicio de la sesión ---")
    except httpx.ConnectError:
        pytest.fail(f"No se pudo conectar a FastAPI en {BASE_URL}. Asegúrate de que uvicorn main:app --reload esté corriendo.")
    
    yield
    
    # 2. Limpiar al finalizar
    client.delete("/limpiar_db")
    print("--- DB Limpiada al finalizar la sesión ---")


@pytest.fixture(scope="function")
def setup_datos_relacionales():
    """Crea Proyectos y Tareas para tests de filtros y resúmenes."""
    client.delete("/limpiar_db")
    
    # --- PROYECTOS ---
    p1 = client.post("/proyectos", json={"nombre": "Proyecto Alpha", "descripcion": "Tareas urgentes"}) # ID 1
    time.sleep(0.01)
    p2 = client.post("/proyectos", json={"nombre": "Proyecto Beta", "descripcion": "Tareas de baja prioridad"}) # ID 2
    time.sleep(0.01)
    p3 = client.post("/proyectos", json={"nombre": "UX/UI Design", "descripcion": "Tareas de diseño"}) # ID 3

    # --- TAREAS ---
    # P1 (Alpha) tiene 4 tareas
    client.post("/proyectos/1/tareas", json={"descripcion": "Definir alcance", "estado": "completada", "prioridad": "alta"}) # ID 1
    client.post("/proyectos/1/tareas", json={"descripcion": "Reunion de equipo", "estado": "en_progreso", "prioridad": "alta"}) # ID 2
    client.post("/proyectos/1/tareas", json={"descripcion": "Analisis de datos", "estado": "pendiente", "prioridad": "media"}) # ID 3
    client.post("/proyectos/1/tareas", json={"descripcion": "Enviar reporte", "estado": "pendiente", "prioridad": "baja"}) # ID 4

    # P2 (Beta) tiene 2 tareas
    client.post("/proyectos/2/tareas", json={"descripcion": "Comprar cafe", "estado": "completada", "prioridad": "baja"}) # ID 5
    client.post("/proyectos/2/tareas", json={"descripcion": "Testear funcionalidad", "estado": "en_progreso", "prioridad": "alta"}) # ID 6

    # P3 (UX/UI) tiene 1 tarea
    client.post("/proyectos/3/tareas", json={"descripcion": "Maquetar landing page", "estado": "pendiente", "prioridad": "media"}) # ID 7
    
    # Resumen esperado:
    # Alpha (1): C:1, EP:1, P:2. Prioridad: Alta:2, Media:1, Baja:1. Total: 4
    # Beta (2): C:1, EP:1, P:0. Prioridad: Baja:1, Alta:1. Total: 2
    # UX/UI (3): C:0, EP:0, P:1. Prioridad: Media:1. Total: 1
    # General: Proyectos: 3. Tareas: 7.

# ------------------------------------------------------------------------------
# 1. TESTS DE PROYECTOS (CRUD, UNICIDAD)
# ------------------------------------------------------------------------------

def test_01_crear_proyecto_exitosamente():
    """POST /proyectos - Creación exitosa (ID 1)."""
    client.delete("/limpiar_db")
    data = {"nombre": "Nuevo Sistema Contable", "descripcion": "Migracion de datos"}
    response = client.post("/proyectos", json=data)
    assert response.status_code == 201
    proj = response.json()
    assert proj["id"] == 1
    assert proj["nombre"] == "Nuevo Sistema Contable"
    assert "fecha_creacion" in proj

def test_02_crear_proyecto_nombre_vacio():
    """POST /proyectos - Debe retornar 422 por nombre vacío."""
    data = {"nombre": "", "descripcion": "Test"}
    response = client.post("/proyectos", json=data)
    assert response.status_code == 422

def test_03_crear_proyecto_duplicado():
    """POST /proyectos - Debe retornar 409 por nombre duplicado (UNIQUE)."""
    data = {"nombre": "Nuevo Sistema Contable"}
    response = client.post("/proyectos", json=data) # Intentar crear el mismo nombre que en test_01
    assert response.status_code == 409
    assert "ya existe" in response.json().get("detail", {}).get("error", "")

def test_04_obtener_proyecto_y_contador():
    """GET /proyectos/{id} - Debe obtener el proyecto 1 y tener 0 tareas."""
    response = client.get("/proyectos/1")
    assert response.status_code == 200
    proj = response.json()
    assert proj["id"] == 1
    assert proj["total_tareas"] == 0 # No hemos añadido tareas aún

def test_05_actualizar_proyecto_existente():
    """PUT /proyectos/{id} - Actualización exitosa."""
    update_data = {"nombre": "Sistema Contable V2.0", "descripcion": "Migracion de datos finalizada"}
    response = client.put("/proyectos/1", json=update_data)
    assert response.status_code == 200
    assert response.json()["nombre"] == "Sistema Contable V2.0"

def test_06_actualizar_proyecto_a_nombre_duplicado():
    """PUT /proyectos/{id} - Debe retornar 409 al intentar duplicar el nombre."""
    client.post("/proyectos", json={"nombre": "Otro Proyecto"}) # ID 2
    update_data = {"nombre": "Otro Proyecto", "descripcion": "Intento de duplicado"}
    response = client.put("/proyectos/1", json=update_data)
    assert response.status_code == 409

# ------------------------------------------------------------------------------
# 2. TESTS DE INTEGRIDAD REFERENCIAL Y TAREAS (1:N)
# ------------------------------------------------------------------------------

def test_07_crear_tarea_en_proyecto_existente():
    """POST /proyectos/{id}/tareas - Creación exitosa (ID 1)."""
    tarea_data = {"descripcion": "Instalar DB", "estado": "pendiente", "prioridad": "alta"}
    response = client.post("/proyectos/1/tareas", json=tarea_data)
    assert response.status_code == 201
    tarea = response.json()
    assert tarea["proyecto_id"] == 1
    assert "proyecto_nombre" in tarea # Verifica que el JOIN funcione
    assert tarea["proyecto_nombre"] == "Sistema Contable V2.0"

def test_08_crear_tarea_en_proyecto_inexistente():
    """POST /proyectos/{id}/tareas - Debe retornar 400 (Fallo Clave Foránea)."""
    tarea_data = {"descripcion": "Tarea huérfana", "estado": "pendiente", "prioridad": "baja"}
    response = client.post("/proyectos/999/tareas", json=tarea_data)
    assert response.status_code == 400
    assert "no existe (Fallo de Clave Foránea)" in response.json().get("detail", {}).get("error", "")

def test_09_eliminar_proyecto_con_cascade():
    """DELETE /proyectos/{id} - Debe eliminar el proyecto y sus tareas asociadas."""
    # Tarea ID 1 fue creada en el proyecto 1
    response_delete = client.delete("/proyectos/1")
    assert response_delete.status_code == 200
    
    # 1. Verificar que el proyecto fue eliminado
    response_get_proj = client.get("/proyectos/1")
    assert response_get_proj.status_code == 404
    
    # 2. Verificar que la tarea también fue eliminada (CASCADE)
    response_get_tarea = client.get("/tareas?proyecto_id=1")
    assert response_get_tarea.status_code == 200
    assert len(response_get_tarea.json()) == 0
    
    # 3. Eliminar proyecto inexistente debe dar 404
    response_404 = client.delete("/proyectos/1")
    assert response_404.status_code == 404

# ------------------------------------------------------------------------------
# 3. TESTS DE FILTROS Y BÚSQUEDAS AVANZADAS
# ------------------------------------------------------------------------------

def test_10_filtrar_proyectos_por_nombre(setup_datos_relacionales):
    """GET /proyectos?nombre=alpha - Debe devolver solo 1 proyecto (Alpha)."""
    response = client.get("/proyectos", params={"nombre": "Alpha"})
    assert response.status_code == 200
    proyectos = response.json()
    assert len(proyectos) == 1
    assert proyectos[0]["nombre"] == "Proyecto Alpha"

def test_11_listar_tareas_de_proyecto_inexistente():
    """GET /proyectos/999/tareas - Debe retornar 404."""
    response = client.get("/proyectos/999/tareas")
    assert response.status_code == 404

def test_12_listar_tareas_de_proyecto_especifico(setup_datos_relacionales):
    """GET /proyectos/1/tareas - Debe devolver 4 tareas de Alpha."""
    response = client.get("/proyectos/1/tareas")
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 4
    assert all(t["proyecto_id"] == 1 for t in tareas)

def test_13_filtrar_todas_las_tareas_por_estado_y_prioridad(setup_datos_relacionales):
    """GET /tareas?estado=pendiente&prioridad=media - Debe devolver 2 tareas (ID 3, 7)."""
    response = client.get("/tareas", params={"estado": "pendiente", "prioridad": "media"})
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 2
    ids = [t['id'] for t in tareas]
    assert 3 in ids and 7 in ids
    
def test_14_filtrar_todas_las_tareas_por_proyecto_id(setup_datos_relacionales):
    """GET /tareas?proyecto_id=2 - Debe devolver 2 tareas del Proyecto Beta (ID 5, 6)."""
    response = client.get("/tareas", params={"proyecto_id": 2})
    assert response.status_code == 200
    tareas = response.json()
    assert len(tareas) == 2
    assert all(t["proyecto_id"] == 2 for t in tareas)

def test_15_ordenamiento_descendente_global(setup_datos_relacionales):
    """GET /tareas?orden=desc - Debe devolver tareas ordenadas de la más reciente (7) a la más antigua (1)."""
    response = client.get("/tareas", params={"orden": "desc"})
    assert response.status_code == 200
    tareas = response.json()
    assert [t['id'] for t in tareas] == [7, 6, 5, 4, 3, 2, 1]

def test_16_mover_tarea_a_otro_proyecto(setup_datos_relacionales):
    """PUT /tareas/{id} - Mover Tarea 1 (Alpha) a Proyecto 2 (Beta)."""
    # Tarea 1 está en Proyecto 1.
    update_data = {"descripcion": "Definir alcance (Movido)", "estado": "completada", "prioridad": "alta", "proyecto_id": 2}
    response = client.put("/tareas/1", json=update_data)
    assert response.status_code == 200
    assert response.json()["proyecto_id"] == 2
    
    # 1. Verificar que ya no está en Proyecto 1
    response_p1 = client.get("/proyectos/1/tareas")
    assert len(response_p1.json()) == 3
    
    # 2. Verificar que ahora está en Proyecto 2
    response_p2 = client.get("/proyectos/2/tareas")
    assert len(response_p2.json()) == 3
    assert any(t["id"] == 1 for t in response_p2.json())

def test_17_mover_tarea_a_proyecto_inexistente():
    """PUT /tareas/{id} - Debe fallar al mover a proyecto 999 (400)."""
    update_data = {"descripcion": "Falla de movimiento", "estado": "completada", "prioridad": "alta", "proyecto_id": 999}
    response = client.put("/tareas/1", json=update_data)
    assert response.status_code == 400
    assert "no existe (Fallo de Clave Foránea)" in response.json().get("detail", {}).get("error", "")

# ------------------------------------------------------------------------------
# 4. TESTS DE RESUMENES Y ESTADÍSTICAS
# ------------------------------------------------------------------------------

def test_18_resumen_proyecto_especifico(setup_datos_relacionales):
    """GET /proyectos/1/resumen - Resumen para Proyecto Alpha (ID 1)."""
    response = client.get("/proyectos/1/resumen")
    assert response.status_code == 200
    resumen = response.json()
    
    assert resumen["proyecto_nombre"] == "Proyecto Alpha"
    assert resumen["total_tareas"] == 4
    
    # Alpha (1): C:1, EP:1, P:2. Prioridad: Alta:2, Media:1, Baja:1. Total: 4
    assert resumen["por_estado"] == {"pendiente": 2, "en_progreso": 1, "completada": 1}
    assert resumen["por_prioridad"] == {"baja": 1, "media": 1, "alta": 2}

def test_19_resumen_proyecto_inexistente():
    """GET /proyectos/999/resumen - Debe retornar 404."""
    response = client.get("/proyectos/999/resumen")
    assert response.status_code == 404

def test_20_resumen_general(setup_datos_relacionales):
    """GET /resumen - Resumen de toda la aplicación."""
    # Tarea 6 está en P2 (Beta). Tarea 1, 2, 3, 4 en P1 (Alpha). Tarea 5 en P2 (Beta). Tarea 7 en P3 (UX/UI)
    # Total Proyectos: 3. Total Tareas: 7.
    # Tareas por estado: Pendiente: 3 (3, 4, 7). En Progreso: 2 (2, 6). Completada: 2 (1, 5).
    # P1 (Alpha) tiene 4 tareas (máximo).
    
    response = client.get("/resumen")
    assert response.status_code == 200
    resumen = response.json()
    
    assert resumen["total_proyectos"] == 3
    assert resumen["total_tareas"] == 7
    
    assert resumen["tareas_por_estado"] == {
        "pendiente": 3, 
        "en_progreso": 2, 
        "completada": 2
    }
    
    assert resumen["proyecto_con_mas_tareas"]["id"] == 1
    assert resumen["proyecto_con_mas_tareas"]["nombre"] == "Proyecto Alpha"
    assert resumen["proyecto_con_mas_tareas"]["cantidad_tareas"] == 4
    
def test_21_resumen_general_sin_tareas():
    """GET /resumen - Caso de borde: 0 tareas."""
    client.delete("/limpiar_db")
    client.post("/proyectos", json={"nombre": "Vacio"}) # ID 1
    
    response = client.get("/resumen")
    assert response.status_code == 200
    resumen = response.json()
    
    assert resumen["total_proyectos"] == 1
    assert resumen["total_tareas"] == 0
    assert resumen["proyecto_con_mas_tareas"]["id"] == 0

#AAAAAAAAAAAAAAAAA