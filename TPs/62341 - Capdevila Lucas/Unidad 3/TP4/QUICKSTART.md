# 🚀 Guía de Inicio Rápido

Pone en marcha la API de Gestión de Proyectos y Tareas en 5 minutos.

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## ⚡ Instalación Rápida

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- FastAPI (framework web)
- Uvicorn (servidor)
- Pydantic (validación)
- Pytest (testing)

### 2. Iniciar el servidor

```bash
python main.py
```

O alternativamente:

```bash
uvicorn main:app --reload
```

Verás un mensaje como:

```
=== API DE GESTIÓN DE PROYECTOS Y TAREAS ===
Visita: http://127.0.0.1:8000/
Documentación: http://127.0.0.1:8000/docs
INFO:     Uvicorn running on http://127.0.0.1:8000
```

¡Listo! El servidor está corriendo 🎉

---

## 🌐 Acceder a la API

### Interfaz Web Interactiva (Swagger UI)

Abre tu navegador y visita:

```
http://127.0.0.1:8000/docs
```

Aquí podrás:
- ✅ Ver todos los endpoints disponibles
- ✅ Probar las peticiones directamente desde el navegador
- ✅ Ver los formatos de request/response
- ✅ Ejecutar ejemplos en tiempo real

### Documentación Alternativa (ReDoc)

```
http://127.0.0.1:8000/redoc
```

---

## 🎯 Primeros Pasos

### Opción 1: Usar la Interfaz Web (Recomendado)

1. Ve a `http://127.0.0.1:8000/docs`
2. Haz clic en **"POST /proyectos"**
3. Haz clic en **"Try it out"**
4. Ingresa:
   ```json
   {
     "nombre": "Mi Primer Proyecto",
     "descripcion": "Proyecto de prueba"
   }
   ```
5. Haz clic en **"Execute"**
6. ¡Verás la respuesta con tu proyecto creado!

### Opción 2: Usar cURL (Terminal)

```bash
# Crear un proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi Proyecto", "descripcion": "Prueba desde terminal"}'

# Listar proyectos
curl http://localhost:8000/proyectos

# Crear una tarea (reemplaza {proyecto_id} con el ID del proyecto creado)
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Mi primera tarea", "prioridad": "alta"}'

# Listar tareas
curl http://localhost:8000/tareas
```

### Opción 3: Usar Python

Crea un archivo `test_api.py`:

```python
import requests

BASE_URL = "http://localhost:8000"

# Crear proyecto
proyecto = requests.post(f"{BASE_URL}/proyectos", json={
    "nombre": "Proyecto desde Python",
    "descripcion": "Prueba con requests"
}).json()

print(f"✅ Proyecto creado: {proyecto}")

# Crear tarea
tarea = requests.post(f"{BASE_URL}/proyectos/{proyecto['id']}/tareas", json={
    "descripcion": "Implementar función",
    "estado": "pendiente",
    "prioridad": "alta"
}).json()

print(f"✅ Tarea creada: {tarea}")

# Ver todas las tareas
tareas = requests.get(f"{BASE_URL}/tareas").json()
print(f"📋 Total de tareas: {len(tareas)}")
```

Ejecuta:
```bash
python test_api.py
```

---

## 🧪 Ejecutar Tests

Verifica que todo funciona correctamente:

```bash
pytest test_TP4.py -v
```

Deberías ver todos los tests pasando (60+ tests):

```
test_TP4.py::test_1_1_tabla_proyectos_existe PASSED
test_TP4.py::test_1_2_tabla_tareas_con_clave_foranea PASSED
test_TP4.py::test_2_1_crear_proyecto_exitoso PASSED
...
========================= 60 passed in 2.50s =========================
```

---

## 📍 Endpoints Principales

Una vez que el servidor esté corriendo, puedes usar estos endpoints:

### Proyectos
- `GET /proyectos` - Listar todos los proyectos
- `POST /proyectos` - Crear proyecto
- `GET /proyectos/{id}` - Ver un proyecto
- `PUT /proyectos/{id}` - Actualizar proyecto
- `DELETE /proyectos/{id}` - Eliminar proyecto

### Tareas
- `GET /tareas` - Listar todas las tareas
- `POST /proyectos/{id}/tareas` - Crear tarea en proyecto
- `GET /proyectos/{id}/tareas` - Listar tareas de un proyecto
- `GET /tareas/{id}` - Ver una tarea
- `PUT /tareas/{id}` - Actualizar tarea
- `DELETE /tareas/{id}` - Eliminar tarea

### Estadísticas
- `GET /resumen` - Resumen general
- `GET /proyectos/{id}/resumen` - Estadísticas del proyecto

---

## 💡 Ejemplos Prácticos

### Crear un proyecto y agregar tareas

```bash
# 1. Crear proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Aplicación Móvil",
    "descripcion": "Desarrollo de app iOS/Android"
  }'

# Respuesta: {"id": 1, "nombre": "Aplicación Móvil", ...}

# 2. Agregar tareas
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar interfaz", "prioridad": "alta"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Implementar login", "estado": "en_progreso"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Escribir tests", "prioridad": "media"}'

# 3. Ver todas las tareas del proyecto
curl http://localhost:8000/proyectos/1/tareas

# 4. Ver estadísticas
curl http://localhost:8000/proyectos/1/resumen
```

### Filtrar tareas

```bash
# Solo tareas completadas
curl "http://localhost:8000/tareas?estado=completada"

# Solo tareas de alta prioridad
curl "http://localhost:8000/tareas?prioridad=alta"

# Tareas completadas de alta prioridad
curl "http://localhost:8000/tareas?estado=completada&prioridad=alta"

# Tareas ordenadas de más antigua a más reciente
curl "http://localhost:8000/tareas?orden=asc"
```

### Actualizar una tarea

```bash
# Cambiar estado a completada
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

# Mover tarea a otro proyecto
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'
```

---

## 🗂️ Archivos Generados

Cuando ejecutes el servidor, se creará automáticamente:

- `tareas.db` - Base de datos SQLite con tus proyectos y tareas

**Nota:** No es necesario crear la base de datos manualmente, se genera automáticamente al iniciar.

---

## 🛑 Detener el Servidor

Presiona `Ctrl + C` en la terminal donde está corriendo el servidor.

---

## ❓ Problemas Comunes

### Error: "Address already in use"

Otro proceso está usando el puerto 8000. Opciones:

1. Detén el otro proceso
2. Usa otro puerto:
   ```bash
   uvicorn main:app --port 8001
   ```

### Error: "Module not found"

Instala las dependencias:
```bash
pip install -r requirements.txt
```

### Error: "Database is locked" (Windows)

Cierra todos los procesos que tengan abierta la base de datos y reinicia el servidor.

### Los tests fallan

Asegúrate de que no haya otra instancia del servidor corriendo y ejecuta:
```bash
pytest test_TP4.py -v --tb=short
```

---

## 🎓 Siguiente Paso

Una vez que hayas probado los ejemplos básicos, revisa el archivo **README.md** para:

- 📖 Documentación técnica completa
- 🏗️ Arquitectura del sistema
- 💾 Estructura de la base de datos
- 📦 Todos los modelos de datos
- 🔌 Referencia completa de endpoints
- 💡 Ejemplos avanzados

---

## 🆘 Ayuda Adicional

- **Documentación interactiva:** `http://127.0.0.1:8000/docs`
- **Documentación alternativa:** `http://127.0.0.1:8000/redoc`
- **Ver README.md** para detalles técnicos completos
- **Ver test_TP4.py** para ejemplos de uso

---

## ✨ Tips Útiles

### Resetear la base de datos

Si quieres empezar de cero:

```bash
# Detén el servidor (Ctrl+C)
# Elimina la base de datos
rm tareas.db  # En Linux/Mac
del tareas.db  # En Windows

# Reinicia el servidor
python main.py
```

### Ver logs en tiempo real

El servidor muestra automáticamente todas las peticiones:

```
INFO:     127.0.0.1:52345 - "POST /proyectos HTTP/1.1" 201 Created
INFO:     127.0.0.1:52346 - "GET /proyectos HTTP/1.1" 200 OK
```

### Modo desarrollo con recarga automática

```bash
uvicorn main:app --reload
```

Cualquier cambio en el código reiniciará automáticamente el servidor.

### Probar con Postman o Insomnia

1. Importa la colección desde `http://127.0.0.1:8000/openapi.json`
2. Todas las rutas estarán disponibles automáticamente

---

## 🎉 ¡Listo para usar!

Ya tienes tu API funcionando. Algunos ejemplos de lo que puedes hacer:

- ✅ Gestionar múltiples proyectos
- ✅ Crear y organizar tareas
- ✅ Filtrar por estado y prioridad
- ✅ Obtener estadísticas en tiempo real
- ✅ Mover tareas entre proyectos
- ✅ Eliminar proyectos con todas sus tareas

**Ejemplo de flujo completo:**

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Crear proyecto
proyecto = requests.post(f"{BASE_URL}/proyectos", json={
    "nombre": "E-commerce",
    "descripcion": "Tienda online"
}).json()

pid = proyecto['id']

# 2. Agregar tareas
tareas = [
    {"descripcion": "Diseño UI/UX", "prioridad": "alta"},
    {"descripcion": "Base de datos", "prioridad": "alta"},
    {"descripcion": "API REST", "estado": "en_progreso", "prioridad": "media"},
    {"descripcion": "Frontend React", "prioridad": "media"},
    {"descripcion": "Testing", "prioridad": "baja"}
]

for tarea in tareas:
    requests.post(f"{BASE_URL}/proyectos/{pid}/tareas", json=tarea)

# 3. Ver resumen
resumen = requests.get(f"{BASE_URL}/proyectos/{pid}/resumen").json()
print(f"📊 Proyecto: {resumen['proyecto_nombre']}")
print(f"📋 Total tareas: {resumen['total_tareas']}")
print(f"✅ Por estado: {resumen['por_estado']}")
print(f"🎯 Por prioridad: {resumen['por_prioridad']}")

# 4. Filtrar tareas de alta prioridad
tareas_alta = requests.get(
    f"{BASE_URL}/proyectos/{pid}/tareas",
    params={"prioridad": "alta"}
).json()

print(f"\n🔥 Tareas de alta prioridad: {len(tareas_alta)}")
for t in tareas_alta:
    print(f"  - {t['descripcion']} [{t['estado']}]")
```

---

**¿Preguntas?** Consulta el README.md o explora la documentación interactiva en `/docs` 📚