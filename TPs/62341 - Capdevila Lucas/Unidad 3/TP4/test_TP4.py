import pytest
from fastapi.testclient import TestClient
from main import app, init_db
from database import DB_NAME
import sqlite3
import os

# Cliente de prueba se crea por test para evitar que quede abierto y bloquee la BD en Windows
@pytest.fixture(autouse=True)
def use_test_client():
    """Create a TestClient per test and expose it as global `client` so existing
    tests can reference the name without changing their signatures.
    The fixture is autouse so it's created after the setup_and_teardown fixture
    (which is defined earlier) and closed before that fixture's teardown runs.
    """
    with TestClient(app) as c:
        globals()['client'] = c
        try:
            yield
        finally:
            # Ensure the global is removed after closing
            globals().pop('client', None)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Configuración antes y después de cada test"""
    # Eliminar base de datos si existe
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    # Inicializar base de datos
    init_db()
    
    yield
    
    # Limpiar después del test
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

# ============== 1. DISEÑO DE BASE DE DATOS RELACIONAL ==============

def test_1_1_tabla_proyectos_existe():
    """Verifica que la tabla proyectos existe con estructura correcta"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar que la tabla existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='proyectos'
    """)
    assert cursor.fetchone() is not None
    
    # Verificar columnas
    cursor.execute("PRAGMA table_info(proyectos)")
    columnas = {col[1]: col for col in cursor.fetchall()}
    
    assert 'id' in columnas
    assert 'nombre' in columnas
    assert 'descripcion' in columnas
    assert 'fecha_creacion' in columnas
    
    # Verificar que nombre no acepta nulos
    assert columnas['nombre'][3] == 1  # notnull
    
    conn.close()

def test_1_2_tabla_tareas_con_clave_foranea():
    """Verifica que la tabla tareas tiene clave foránea a proyectos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar que la tabla existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='tareas'
    """)
    assert cursor.fetchone() is not None
    
    # Verificar columnas
    cursor.execute("PRAGMA table_info(tareas)")
    columnas = {col[1]: col for col in cursor.fetchall()}
    
    assert 'proyecto_id' in columnas
    
    # Verificar clave foránea
    cursor.execute("PRAGMA foreign_key_list(tareas)")
    foreign_keys = cursor.fetchall()
    
    assert len(foreign_keys) > 0
    assert foreign_keys[0][2] == 'proyectos'  # tabla referenciada
    assert foreign_keys[0][3] == 'proyecto_id'  # columna local
    
    conn.close()

# ============== 2. CRUD DE PROYECTOS ==============

def test_2_1_crear_proyecto_exitoso():
    """Test: Crear un proyecto válido"""
    response = client.post("/proyectos", json={
        "nombre": "Proyecto Test",
        "descripcion": "Descripción de prueba"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Proyecto Test"
    assert data["descripcion"] == "Descripción de prueba"
    assert "fecha_creacion" in data
    assert "id" in data

def test_2_2_crear_proyecto_nombre_duplicado():
    """Test: Intentar crear proyecto con nombre duplicado debe fallar"""
    # Crear primer proyecto
    client.post("/proyectos", json={
        "nombre": "Proyecto Único",
        "descripcion": "Primera vez"
    })
    
    # Intentar crear segundo proyecto con mismo nombre
    response = client.post("/proyectos", json={
        "nombre": "Proyecto Único",
        "descripcion": "Segunda vez"
    })
    
    assert response.status_code == 409

def test_2_3_listar_proyectos():
    """Test: Listar todos los proyectos"""
    # Crear varios proyectos
    client.post("/proyectos", json={"nombre": "Proyecto A"})
    client.post("/proyectos", json={"nombre": "Proyecto B"})
    
    response = client.get("/proyectos")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_2_4_obtener_proyecto_con_contador():
    """Test: Obtener proyecto específico con contador de tareas"""
    # Crear proyecto
    response = client.post("/proyectos", json={"nombre": "Proyecto Counter"})
    proyecto_id = response.json()["id"]
    
    # Crear tareas
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 1"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 2"
    })
    
    # Obtener proyecto
    response = client.get(f"/proyectos/{proyecto_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_tareas"] == 2

def test_2_5_actualizar_proyecto():
    """Test: Actualizar proyecto existente"""
    # Crear proyecto
    response = client.post("/proyectos", json={"nombre": "Proyecto Original"})
    proyecto_id = response.json()["id"]
    
    # Actualizar
    response = client.put(f"/proyectos/{proyecto_id}", json={
        "nombre": "Proyecto Modificado",
        "descripcion": "Nueva descripción"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Proyecto Modificado"
    assert data["descripcion"] == "Nueva descripción"

def test_2_6_eliminar_proyecto_y_tareas_cascade():
    """Test: Eliminar proyecto debe eliminar tareas (CASCADE)"""
    # Crear proyecto
    response = client.post("/proyectos", json={"nombre": "Proyecto a Eliminar"})
    proyecto_id = response.json()["id"]
    
    # Crear tareas
    client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Tarea 1"})
    client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Tarea 2"})
    
    # Eliminar proyecto
    response = client.delete(f"/proyectos/{proyecto_id}")
    
    assert response.status_code == 200
    assert response.json()["tareas_eliminadas"] == 2
    
    # Verificar que tareas fueron eliminadas
    response = client.get("/tareas")
    assert len(response.json()) == 0

# ============== 3. TAREAS ASOCIADAS A PROYECTOS ==============

def test_3_1_crear_tarea_en_proyecto():
    """Test: Crear tarea dentro de un proyecto"""
    # Crear proyecto
    response = client.post("/proyectos", json={"nombre": "Proyecto para Tareas"})
    proyecto_id = response.json()["id"]
    
    # Crear tarea
    response = client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Mi tarea",
        "estado": "pendiente",
        "prioridad": "alta"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["descripcion"] == "Mi tarea"
    assert data["proyecto_id"] == proyecto_id

def test_3_2_crear_tarea_proyecto_inexistente():
    """Test: Intentar crear tarea en proyecto inexistente debe fallar"""
    response = client.post("/proyectos/999/tareas", json={
        "descripcion": "Tarea huérfana"
    })
    
    assert response.status_code == 400

def test_3_3_listar_tareas_de_proyecto():
    """Test: Listar tareas de un proyecto específico"""
    # Crear proyectos
    r1 = client.post("/proyectos", json={"nombre": "Proyecto 1"})
    r2 = client.post("/proyectos", json={"nombre": "Proyecto 2"})
    
    proyecto_id_1 = r1.json()["id"]
    proyecto_id_2 = r2.json()["id"]
    
    # Crear tareas en proyecto 1
    client.post(f"/proyectos/{proyecto_id_1}/tareas", json={"descripcion": "Tarea P1-1"})
    client.post(f"/proyectos/{proyecto_id_1}/tareas", json={"descripcion": "Tarea P1-2"})
    
    # Crear tarea en proyecto 2
    client.post(f"/proyectos/{proyecto_id_2}/tareas", json={"descripcion": "Tarea P2-1"})
    
    # Listar tareas del proyecto 1
    response = client.get(f"/proyectos/{proyecto_id_1}/tareas")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_3_4_listar_tareas_proyecto_inexistente():
    """Test: Listar tareas de proyecto inexistente debe devolver 404"""
    response = client.get("/proyectos/999/tareas")
    assert response.status_code == 404

def test_3_5_actualizar_tarea_cambiar_proyecto():
    """Test: Actualizar tarea y moverla a otro proyecto"""
    # Crear dos proyectos
    r1 = client.post("/proyectos", json={"nombre": "Proyecto Origen"})
    r2 = client.post("/proyectos", json={"nombre": "Proyecto Destino"})
    
    proyecto_id_1 = r1.json()["id"]
    proyecto_id_2 = r2.json()["id"]
    
    # Crear tarea en proyecto 1
    response = client.post(f"/proyectos/{proyecto_id_1}/tareas", json={
        "descripcion": "Tarea a mover"
    })
    tarea_id = response.json()["id"]
    
    # Mover tarea al proyecto 2
    response = client.put(f"/tareas/{tarea_id}", json={
        "proyecto_id": proyecto_id_2
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["proyecto_id"] == proyecto_id_2

def test_3_6_eliminar_tarea():
    """Test: Eliminar una tarea específica"""
    # Crear proyecto y tarea
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    response = client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea a eliminar"
    })
    tarea_id = response.json()["id"]
    
    # Eliminar tarea
    response = client.delete(f"/tareas/{tarea_id}")
    
    assert response.status_code == 200
    
    # Verificar que fue eliminada
    response = client.get("/tareas")
    assert len(response.json()) == 0

# ============== 4. FILTROS Y BÚSQUEDAS AVANZADAS ==============

def test_4_1_filtrar_proyectos_por_nombre():
    """Test: Buscar proyectos por nombre parcial"""
    client.post("/proyectos", json={"nombre": "Desarrollo Web"})
    client.post("/proyectos", json={"nombre": "Desarrollo Mobile"})
    client.post("/proyectos", json={"nombre": "Marketing Digital"})
    
    response = client.get("/proyectos?nombre=Desarrollo")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_4_2_filtrar_tareas_por_estado():
    """Test: Filtrar tareas por estado"""
    # Crear proyecto
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    # Crear tareas con diferentes estados
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 1",
        "estado": "pendiente"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 2",
        "estado": "completada"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 3",
        "estado": "completada"
    })
    
    response = client.get("/tareas?estado=completada")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_4_3_filtrar_tareas_por_prioridad():
    """Test: Filtrar tareas por prioridad"""
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea alta",
        "prioridad": "alta"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea baja",
        "prioridad": "baja"
    })
    
    response = client.get("/tareas?prioridad=alta")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["prioridad"] == "alta"

def test_4_4_filtros_multiples_combinados():
    """Test: Combinar múltiples filtros simultáneamente"""
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 1",
        "estado": "completada",
        "prioridad": "alta"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 2",
        "estado": "completada",
        "prioridad": "baja"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea 3",
        "estado": "pendiente",
        "prioridad": "alta"
    })
    
    response = client.get("/tareas?estado=completada&prioridad=alta")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["estado"] == "completada"
    assert data[0]["prioridad"] == "alta"

def test_4_5_ordenar_tareas_ascendente():
    """Test: Ordenar tareas por fecha ascendente"""
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    r1 = client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Primera"})
    r2 = client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Segunda"})
    r3 = client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Tercera"})
    
    response = client.get("/tareas?orden=asc")
    
    assert response.status_code == 200
    data = response.json()
    assert data[0]["descripcion"] == "Primera"
    assert data[-1]["descripcion"] == "Tercera"

def test_4_6_ordenar_tareas_descendente():
    """Test: Ordenar tareas por fecha descendente (más recientes primero)"""
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Primera"})
    client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Segunda"})
    client.post(f"/proyectos/{proyecto_id}/tareas", json={"descripcion": "Tercera"})
    
    response = client.get("/tareas?orden=desc")
    
    assert response.status_code == 200
    data = response.json()
    assert data[0]["descripcion"] == "Tercera"
    assert data[-1]["descripcion"] == "Primera"

# ============== 5. ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ==============

def test_5_1_resumen_proyecto():
    """Test: Obtener resumen estadístico de un proyecto"""
    response = client.post("/proyectos", json={"nombre": "Proyecto Stats"})
    proyecto_id = response.json()["id"]
    
    # Crear tareas variadas
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "T1",
        "estado": "pendiente",
        "prioridad": "alta"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "T2",
        "estado": "completada",
        "prioridad": "baja"
    })
    client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "T3",
        "estado": "completada",
        "prioridad": "alta"
    })
    
    response = client.get(f"/proyectos/{proyecto_id}/resumen")
    
    assert response.status_code == 200
    data = response.json()
    assert data["proyecto_id"] == proyecto_id
    assert data["proyecto_nombre"] == "Proyecto Stats"
    assert data["total_tareas"] == 3
    assert data["por_estado"]["pendiente"] == 1
    assert data["por_estado"]["completada"] == 2
    assert data["por_prioridad"]["alta"] == 2
    assert data["por_prioridad"]["baja"] == 1

def test_5_2_resumen_proyecto_inexistente():
    """Test: Resumen de proyecto inexistente debe devolver 404"""
    response = client.get("/proyectos/999/resumen")
    assert response.status_code == 404

def test_5_3_resumen_general():
    """Test: Obtener resumen general de la aplicación"""
    # Crear proyectos
    r1 = client.post("/proyectos", json={"nombre": "Proyecto A"})
    r2 = client.post("/proyectos", json={"nombre": "Proyecto B"})
    
    proyecto_id_1 = r1.json()["id"]
    proyecto_id_2 = r2.json()["id"]
    
    # Crear tareas en proyecto 1
    for i in range(5):
        client.post(f"/proyectos/{proyecto_id_1}/tareas", json={
            "descripcion": f"Tarea {i}",
            "estado": "pendiente"
        })
    
    # Crear tareas en proyecto 2
    for i in range(3):
        client.post(f"/proyectos/{proyecto_id_2}/tareas", json={
            "descripcion": f"Tarea {i}",
            "estado": "completada"
        })
    
    response = client.get("/resumen")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_proyectos"] == 2
    assert data["total_tareas"] == 8
    assert data["tareas_por_estado"]["pendiente"] == 5
    assert data["tareas_por_estado"]["completada"] == 3
    assert data["proyecto_con_mas_tareas"]["id"] == proyecto_id_1
    assert data["proyecto_con_mas_tareas"]["cantidad_tareas"] == 5

def test_5_4_resumen_general_vacio():
    """Test: Resumen general sin proyectos"""
    response = client.get("/resumen")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_proyectos"] == 0
    assert data["total_tareas"] == 0

# ============== 6. VALIDACIÓN CON PYDANTIC MODELS ==============

def test_6_1_validacion_proyecto_nombre_vacio():
    """Test: Validar que nombre de proyecto no puede estar vacío"""
    response = client.post("/proyectos", json={
        "nombre": "   ",
        "descripcion": "Test"
    })
    
    assert response.status_code == 422

def test_6_2_validacion_tarea_descripcion_vacia():
    """Test: Validar que descripción de tarea no puede estar vacía"""
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    response = client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": ""
    })
    
    assert response.status_code == 422

def test_6_3_validacion_estado_invalido():
    """Test: Validar estados válidos"""
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    response = client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea",
        "estado": "estado_invalido"
    })
    
    assert response.status_code == 422

def test_6_4_validacion_prioridad_invalida():
    """Test: Validar prioridades válidas"""
    response = client.post("/proyectos", json={"nombre": "Proyecto"})
    proyecto_id = response.json()["id"]
    
    response = client.post(f"/proyectos/{proyecto_id}/tareas", json={
        "descripcion": "Tarea",
        "prioridad": "super_alta"
    })
    
    assert response.status_code == 422

# ============== 7. MANEJO DE ERRORES ESPECÍFICOS ==============

def test_7_1_error_404_proyecto_no_encontrado():
    """Test: Error 404 cuando proyecto no existe"""
    response = client.get("/proyectos/999")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data

def test_7_2_error_404_tarea_no_encontrada():
    """Test: Error 404 cuando tarea no existe"""
    response = client.put("/tareas/999", json={
        "descripcion": "Actualización"
    })
    
    assert response.status_code == 404

def test_7_3_error_400_datos_invalidos():
    """Test: Error 400 para datos inválidos (proyecto_id inexistente)"""
    response = client.post("/proyectos/999/tareas", json={
        "descripcion": "Tarea"
    })
    
    assert response.status_code == 400

def test_7_4_error_409_nombre_duplicado():
    """Test: Error 409 para conflicto de nombre duplicado"""
    client.post("/proyectos", json={"nombre": "Proyecto Único"})
    response = client.post("/proyectos", json={"nombre": "Proyecto Único"})
    
    assert response.status_code == 409

# ============== 8. VERIFICACIÓN DE INTEGRIDAD REFERENCIAL ==============

def test_8_1_integridad_crear_proyecto_y_tareas():
    """Test: Crear proyecto y agregarle varias tareas"""
    response = client.post("/proyectos", json={"nombre": "Proyecto Integral"})
    proyecto_id = response.json()["id"]
    
    # Agregar múltiples tareas
    tareas_creadas = []
    for i in range(5):
        response = client.post(f"/proyectos/{proyecto_id}/tareas", json={
            "descripcion": f"Tarea {i+1}"
        })
        assert response.status_code == 201
        tareas_creadas.append(response.json()["id"])
    
    # Verificar que todas las tareas existen
    response = client.get(f"/proyectos/{proyecto_id}/tareas")
    assert len(response.json()) == 5

def test_8_2_integridad_eliminar_proyecto_elimina_tareas():
    """Test: Eliminar proyecto elimina sus tareas (CASCADE)"""
    # Crear proyecto con tareas
    response = client.post("/proyectos", json={"nombre": "Proyecto a Eliminar"})
    proyecto_id = response.json()["id"]
    
    for i in range(3):
        client.post(f"/proyectos/{proyecto_id}/tareas", json={
            "descripcion": f"Tarea {i+1}"
        })
    
    # Verificar que hay 3 tareas
    response = client.get("/tareas")
    assert len(response.json()) == 3
    
    # Eliminar proyecto
    client.delete(f"/proyectos/{proyecto_id}")
    
    # Verificar que no quedan tareas
    response = client.get("/tareas")
    assert len(response.json()) == 0

def test_8_3_integridad_tarea_proyecto_inexistente_falla():
    """Test: No se puede crear tarea con proyecto_id inexistente"""
    response = client.post("/proyectos/999/tareas", json={
        "descripcion": "Tarea huérfana"
    })
    
    assert response.status_code == 400

def test_8_4_integridad_mover_tarea_entre_proyectos():
    """Test: Modificar proyecto_id de tarea para moverla"""
    # Crear dos proyectos
    r1 = client.post("/proyectos", json={"nombre": "Proyecto 1"})
    r2 = client.post("/proyectos", json={"nombre": "Proyecto 2"})
    
    proyecto_id_1 = r1.json()["id"]
    proyecto_id_2 = r2.json()["id"]
    
    # Crear tarea en proyecto 1
    response = client.post(f"/proyectos/{proyecto_id_1}/tareas", json={
        "descripcion": "Tarea móvil"
    })
    tarea_id = response.json()["id"]
    
    # Verificar que está en proyecto 1
    response = client.get(f"/proyectos/{proyecto_id_1}/tareas")
    assert len(response.json()) == 1
    
    # Mover a proyecto 2
    response = client.put(f"/tareas/{tarea_id}", json={
        "proyecto_id": proyecto_id_2
    })
    assert response.status_code == 200
    
    # Verificar que ahora está en proyecto 2
    response = client.get(f"/proyectos/{proyecto_id_2}/tareas")
    assert len(response.json()) == 1
    
    # Verificar que ya no está en proyecto 1
    response = client.get(f"/proyectos/{proyecto_id_1}/tareas")
    assert len(response.json()) == 0

# ============== TESTS ADICIONALES ==============

def test_9_1_listar_todas_las_tareas():
    """Test: Listar todas las tareas de todos los proyectos"""
    # Crear proyectos
    r1 = client.post("/proyectos", json={"nombre": "Proyecto 1"})
    r2 = client.post("/proyectos", json={"nombre": "Proyecto 2"})
    
    proyecto_id_1 = r1.json()["id"]
    proyecto_id_2 = r2.json()["id"]
    
    # Crear tareas en ambos proyectos
    client.post(f"/proyectos/{proyecto_id_1}/tareas", json={"descripcion": "Tarea P1"})
    client.post(f"/proyectos/{proyecto_id_2}/tareas", json={"descripcion": "Tarea P2"})
    
    # Listar todas
    response = client.get("/tareas")
    
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_9_2_filtrar_tareas_por_proyecto_id():
    """Test: Filtrar tareas por proyecto_id en endpoint /tareas"""
    r1 = client.post("/proyectos", json={"nombre": "Proyecto 1"})
    r2 = client.post("/proyectos", json={"nombre": "Proyecto 2"})
    
    proyecto_id_1 = r1.json()["id"]
    proyecto_id_2 = r2.json()["id"]
    
    client.post(f"/proyectos/{proyecto_id_1}/tareas", json={"descripcion": "Tarea P1"})
    client.post(f"/proyectos/{proyecto_id_2}/tareas", json={"descripcion": "Tarea P2"})
    
    # Filtrar por proyecto 1
    response = client.get(f"/tareas?proyecto_id={proyecto_id_1}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["proyecto_id"] == proyecto_id_1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])