import pytest
from fastapi.testclient import TestClient
from main import app, init_db, DB_NAME
import sqlite3
import os

# Cliente de prueba
client = TestClient(app)

# ============== FIXTURES ==============

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Se ejecuta antes y después de cada test"""
    # Antes del test: eliminar base de datos si existe
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    # Inicializar base de datos limpia
    init_db()
    
    yield
    
    # Después del test: limpiar
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

# ============== TESTS DE MIGRACIÓN A SQLite ==============

def test_base_datos_se_crea():
    assert os.path.exists(DB_NAME), "La base de datos tareas.db no existe"

def test_tabla_tareas_existe():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='tareas'
    """)
    tabla = cursor.fetchone()
    assert tabla is not None, "La tabla 'tareas' no existe"
    cursor.execute("PRAGMA table_info(tareas)")
    columnas = cursor.fetchall()
    nombres_columnas = [col[1] for col in columnas]
    assert "id" in nombres_columnas
    assert "descripcion" in nombres_columnas
    assert "estado" in nombres_columnas
    assert "fecha_creacion" in nombres_columnas
    assert "prioridad" in nombres_columnas
    columna_id = [col for col in columnas if col[1] == "id"][0]
    assert columna_id[5] == 1, "id debe ser PRIMARY KEY"
    columna_descripcion = [col for col in columnas if col[1] == "descripcion"][0]
    columna_estado = [col for col in columnas if col[1] == "estado"][0]
    assert columna_descripcion[3] == 1
    assert columna_estado[3] == 1
    conn.close()

# ============== TESTS DE CRUD PERSISTENTE ==============

def test_crear_tarea():
    response = client.post("/tareas", json={
        "descripcion": "Tarea de prueba",
        "estado": "pendiente",
        "prioridad": "media"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["descripcion"] == "Tarea de prueba"
    assert data["estado"] == "pendiente"
    assert data["prioridad"] == "media"
    assert "fecha_creacion" in data

def test_crear_tarea_descripcion_vacia():
    response = client.post("/tareas", json={
        "descripcion": "",
        "estado": "pendiente"
    })
    assert response.status_code == 422

def test_crear_tarea_descripcion_solo_espacios():
    response = client.post("/tareas", json={
        "descripcion": "   ",
        "estado": "pendiente"
    })
    assert response.status_code == 422

def test_crear_tarea_estado_invalido():
    response = client.post("/tareas", json={
        "descripcion": "Tarea",
        "estado": "invalido"
    })
    assert response.status_code == 422

def test_crear_tarea_estados_validos():
    estados_validos = ["pendiente", "en_progreso", "completada"]
    for estado in estados_validos:
        response = client.post("/tareas", json={
            "descripcion": f"Tarea {estado}",
            "estado": estado
        })
        assert response.status_code == 201
        assert response.json()["estado"] == estado

def test_obtener_todas_tareas():
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "completada"})
    response = client.get("/tareas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_actualizar_tarea():
    crear_response = client.post("/tareas", json={"descripcion": "Tarea original", "estado": "pendiente"})
    tarea_id = crear_response.json()["id"]
    response = client.put(f"/tareas/{tarea_id}", json={
        "descripcion": "Tarea actualizada",
        "estado": "completada"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["descripcion"] == "Tarea actualizada"
    assert data["estado"] == "completada"

def test_actualizar_tarea_inexistente():
    response = client.put("/tareas/999", json={"descripcion": "No existe", "estado": "pendiente"})
    assert response.status_code == 404
    assert "error" in response.json()["detail"]

def test_eliminar_tarea():
    crear_response = client.post("/tareas", json={"descripcion": "Tarea a eliminar", "estado": "pendiente"})
    tarea_id = crear_response.json()["id"]
    response = client.delete(f"/tareas/{tarea_id}")
    assert response.status_code == 200
    get_response = client.get("/tareas")
    assert len(get_response.json()) == 0

def test_eliminar_tarea_inexistente():
    response = client.delete("/tareas/999")
    assert response.status_code == 404

# ============== TESTS DE PERSISTENCIA ==============

def test_persistencia_datos():
    client.post("/tareas", json={"descripcion": "Tarea persistente", "estado": "pendiente", "prioridad": "alta"})
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE descripcion = 'Tarea persistente'")
    tarea = cursor.fetchone()
    conn.close()
    assert tarea is not None
    assert tarea[1] == "Tarea persistente"
    assert tarea[2] == "pendiente"

def test_datos_persisten_tras_reinicio():
    client.post("/tareas", json={"descripcion": "Tarea antes de reinicio", "estado": "pendiente"})
    nuevo_client = TestClient(app)
    response = nuevo_client.get("/tareas")
    tareas = response.json()
    assert len(tareas) >= 1
    assert any(t["descripcion"] == "Tarea antes de reinicio" for t in tareas)

# ============== TESTS DE FILTROS ==============

def test_filtro_por_estado():
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "completada"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "estado": "pendiente"})
    response = client.get("/tareas?estado=pendiente")
    tareas = response.json()
    assert len(tareas) == 2
    assert all(t["estado"] == "pendiente" for t in tareas)

def test_filtro_por_texto():
    client.post("/tareas", json={"descripcion": "Comprar pan", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Estudiar Python", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Comprar leche", "estado": "pendiente"})
    response = client.get("/tareas?texto=comprar")
    tareas = response.json()
    assert len(tareas) == 2
    assert all("comprar" in t["descripcion"].lower() for t in tareas)

def test_filtro_por_prioridad():
    client.post("/tareas", json={"descripcion": "Tarea 1", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "prioridad": "baja"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "prioridad": "alta"})
    response = client.get("/tareas?prioridad=alta")
    tareas = response.json()
    assert len(tareas) == 2
    assert all(t["prioridad"] == "alta" for t in tareas)

def test_ordenamiento_descendente():
    import time
    client.post("/tareas", json={"descripcion": "Primera"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Segunda"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Tercera"})
    response = client.get("/tareas?orden=desc")
    tareas = response.json()
    assert tareas[0]["descripcion"] == "Tercera"
    assert tareas[-1]["descripcion"] == "Primera"

def test_ordenamiento_ascendente():
    import time
    client.post("/tareas", json={"descripcion": "Primera"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Segunda"})
    time.sleep(0.1)
    client.post("/tareas", json={"descripcion": "Tercera"})
    response = client.get("/tareas?orden=asc")
    tareas = response.json()
    assert tareas[0]["descripcion"] == "Primera"
    assert tareas[-1]["descripcion"] == "Tercera"

def test_filtros_combinados():
    client.post("/tareas", json={"descripcion": "Comprar pan urgente", "estado": "pendiente", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "Comprar leche", "estado": "completada", "prioridad": "baja"})
    client.post("/tareas", json={"descripcion": "Estudiar", "estado": "pendiente", "prioridad": "alta"})
    response = client.get("/tareas?estado=pendiente&prioridad=alta&texto=comprar")
    tareas = response.json()
    assert len(tareas) == 1
    assert tareas[0]["descripcion"] == "Comprar pan urgente"

# ============== TESTS DE MEJORAS ==============

def test_endpoint_resumen():
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "pendiente", "prioridad": "baja"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "T4", "estado": "en_progreso", "prioridad": "media"})
    response = client.get("/tareas/resumen")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tareas"] == 4
    assert data["por_estado"]["pendiente"] == 2
    assert data["por_estado"]["completada"] == 1
    assert data["por_estado"]["en_progreso"] == 1
    assert data["por_prioridad"]["alta"] == 2
    assert data["por_prioridad"]["baja"] == 1
    assert data["por_prioridad"]["media"] == 1

def test_campo_prioridad_existe():
    response = client.post("/tareas", json={"descripcion": "Tarea con prioridad", "estado": "pendiente", "prioridad": "alta"})
    assert response.status_code == 201
    data = response.json()
    assert "prioridad" in data
    assert data["prioridad"] == "alta"

def test_prioridades_validas():
    for prioridad in ["baja", "media", "alta"]:
        response = client.post("/tareas", json={"descripcion": f"Tarea {prioridad}", "prioridad": prioridad})
        assert response.status_code == 201

def test_prioridad_invalida():
    response = client.post("/tareas", json={"descripcion": "Tarea", "prioridad": "urgente"})
    assert response.status_code == 422

def test_validacion_con_pydantic():
    response = client.post("/tareas", json={"estado": "pendiente"})
    assert response.status_code == 422

def test_completar_todas_tareas():
    """PUT /tareas/completar_todas - Marcar todas como completadas"""
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada"})
    response = client.put("/tareas/completar_todas", json={})
    assert response.status_code == 200
    data = response.json()
    assert "mensaje" in data
    todas = client.get("/tareas").json()
    assert all(t["estado"] == "completada" for t in todas)

# ============== TEST DE ENDPOINT RAÍZ ==============

def test_endpoint_raiz():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "nombre" in data or "endpoints" in data

# ============== EJECUCIÓN DIRECTA ==============

if __name__ == "__main__":
    print("=" * 70)
    print("TESTS DEL TP3 - API DE TAREAS PERSISTENTE")
    print("=" * 70)
    pytest.main([__file__, "-v", "--tb=short"])
