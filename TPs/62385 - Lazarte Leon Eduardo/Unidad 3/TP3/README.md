# 📝 TP3 - API de Tareas Persistente con SQLite

## 📋 Descripción
API REST desarrollada con **FastAPI** que permite gestionar tareas de forma persistente usando **SQLite**. Los datos se mantienen almacenados incluso después de reiniciar el servidor.

---

## 🚀 Instalación y Configuración

### ✅ Requisitos Previos
- **Python 3.8 o superior**
- **pip** (gestor de paquetes de Python)

### 📦 Paso 1: Descargar los archivos
Asegúrate de tener los siguientes archivos en la carpeta `TP3`:
```
TP3/
├── main.py              # Código principal de la API
├── test_TP3.py          # Tests automatizados
├── requirements.txt     # Dependencias del proyecto
└── README.md            # Este archivo
```

### 🔧 Paso 2: Instalar dependencias

Abre una terminal en la carpeta `TP3` y ejecuta:

```bash
pip install -r requirements.txt
```

Esto instalará automáticamente:
- `fastapi==0.103.2` - Framework para crear la API
- `uvicorn==0.23.2` - Servidor ASGI para ejecutar FastAPI
- `httpx==0.24.1` - Cliente HTTP para testing
- `requests==2.31.0` - Biblioteca de solicitudes HTTP
- `pytest==7.4.2` - Framework de testing

---

## ▶️ Ejecutar el Servidor

### Iniciar la API

En la terminal, dentro de la carpeta `TP3`, ejecuta:

```bash
uvicorn main:app --reload
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
✅ Base de datos inicializada correctamente
INFO:     Application startup complete.
```

El servidor estará disponible en: **`http://localhost:8000`**

---

## 📚 Documentación Interactiva

Una vez que el servidor esté corriendo, accede a:

### 🌐 Swagger UI (Recomendado)
```
http://localhost:8000/docs
```
Interfaz interactiva donde puedes **probar todos los endpoints** directamente desde el navegador.

### 📖 ReDoc
```
http://localhost:8000/redoc
```
Documentación alternativa con un diseño más limpio.

---

## 🧪 Ejecutar Tests Automatizados

### ⚠️ Importante: Servidor debe estar corriendo
Los tests necesitan que el servidor esté activo.

### Paso 1: Abrir una terminal para el servidor
```bash
uvicorn main:app --reload
```
*Deja esta terminal abierta*

### Paso 2: Abrir OTRA terminal para los tests
En una **nueva terminal**, navega a la carpeta `TP3` y ejecuta:

#### ✅ Ejecutar TODOS los tests
```bash
pytest test_TP3.py -v
```

#### ✅ Ejecutar un test específico
```bash
pytest test_TP3.py::test_crear_tarea -v
```

#### ✅ Ver más detalles de los errores
```bash
pytest test_TP3.py -vv --tb=short
```

### 📊 Salida esperada (todos los tests pasan):
```
test_TP3.py::test_base_datos_se_crea PASSED                                  [ 3%]
test_TP3.py::test_tabla_tareas_existe PASSED                                 [ 7%]
test_TP3.py::test_crear_tarea PASSED                                         [11%]
test_TP3.py::test_crear_tarea_descripcion_vacia PASSED                       [14%]
...
======================== 27 passed in 2.45s ========================
```

---

## 🔗 Endpoints Disponibles

### 📄 Endpoint Raíz
```http
GET /
```
Devuelve información general de la API.

---

### 📋 Gestión de Tareas

#### 1. **Listar todas las tareas**
```http
GET /tareas
```

**Query Parameters (opcionales):**
- `estado` - Filtra por estado: `pendiente`, `en_progreso`, `completada`
- `texto` - Busca en la descripción
- `prioridad` - Filtra por prioridad: `baja`, `media`, `alta`
- `orden` - Ordena por fecha: `asc` (ascendente) o `desc` (descendente)

**Ejemplos:**
```bash
# Todas las tareas
curl http://localhost:8000/tareas

# Solo pendientes
curl http://localhost:8000/tareas?estado=pendiente

# Buscar "comprar" con prioridad alta
curl http://localhost:8000/tareas?texto=comprar&prioridad=alta

# Ordenar más recientes primero
curl http://localhost:8000/tareas?orden=desc
```

---

#### 2. **Crear una nueva tarea**
```http
POST /tareas
```

**Body (JSON):**
```json
{
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Campos:**
- `descripcion` (obligatorio) - No puede estar vacío
- `estado` (opcional) - Valores: `pendiente`, `en_progreso`, `completada` (default: `pendiente`)
- `prioridad` (opcional) - Valores: `baja`, `media`, `alta` (default: `media`)

**Ejemplo con curl:**
```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Estudiar FastAPI","estado":"en_progreso","prioridad":"alta"}'
```

**Respuesta (201 Created):**
```json
{
  "id": 1,
  "descripcion": "Estudiar FastAPI",
  "estado": "en_progreso",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-16 18:30:00"
}
```

---

#### 3. **Obtener una tarea específica**
```http
GET /tareas/{id}
```

**Ejemplo:**
```bash
curl http://localhost:8000/tareas/1
```

---

#### 4. **Actualizar una tarea**
```http
PUT /tareas/{id}
```

**Body (JSON) - Todos los campos son opcionales:**
```json
{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "baja"
}
```

**Ejemplo:**
```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado":"completada"}'
```

---

#### 5. **Eliminar una tarea**
```http
DELETE /tareas/{id}
```

**Ejemplo:**
```bash
curl -X DELETE http://localhost:8000/tareas/1
```

---

#### 6. **Completar todas las tareas**
```http
PUT /tareas/completar_todas
```

Marca TODAS las tareas como completadas.

**Ejemplo:**
```bash
curl -X PUT http://localhost:8000/tareas/completar_todas
```

**Respuesta:**
```json
{
  "mensaje": "Todas las tareas han sido marcadas como completadas",
  "tareas_actualizadas": 5
}
```

---

#### 7. **Obtener resumen de tareas**
```http
GET /tareas/resumen
```

Devuelve estadísticas agrupadas por estado y prioridad.

**Ejemplo:**
```bash
curl http://localhost:8000/tareas/resumen
```

**Respuesta:**
```json
{
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 3,
    "completada": 2
  },
  "por_prioridad": {
    "baja": 2,
    "media": 5,
    "alta": 3
  }
}
```

---

## 📊 Modelo de Datos

### Estructura de una Tarea
```json
{
  "id": 1,
  "descripcion": "Descripción de la tarea",
  "estado": "pendiente",
  "prioridad": "media",
  "fecha_creacion": "2025-10-16 15:30:00"
}
```

**Campos:**
- `id` - Integer (generado automáticamente)
- `descripcion` - String (obligatorio, mínimo 1 carácter)
- `estado` - Enum: `"pendiente"`, `"en_progreso"`, `"completada"`
- `prioridad` - Enum: `"baja"`, `"media"`, `"alta"`
- `fecha_creacion` - String (generado automáticamente en formato ISO)

---

## ✅ Validaciones Implementadas

- ✔️ La descripción **no puede estar vacía** ni contener solo espacios
- ✔️ El estado solo acepta: `pendiente`, `en_progreso`, `completada`
- ✔️ La prioridad solo acepta: `baja`, `media`, `alta`
- ✔️ Manejo de errores **404** para tareas inexistentes
- ✔️ Validación automática con **Pydantic Models**

---

## 💾 Persistencia de Datos

Los datos se almacenan en el archivo **`tareas.db`** (SQLite) que se crea automáticamente al iniciar el servidor.

### Verificar la persistencia:

1. **Crear algunas tareas** usando la API
2. **Detener el servidor** (Ctrl+C en la terminal)
3. **Volver a iniciar** el servidor
4. **Verificar** que las tareas siguen disponibles

```bash
# 1. Crear una tarea
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Esta tarea persiste"}'

# 2. Detener servidor (Ctrl+C)

# 3. Reiniciar servidor
uvicorn main:app --reload

# 4. Verificar que sigue ahí
curl http://localhost:8000/tareas
```

---

## 🌟 Mejoras Implementadas (Obligatorias)

1. ✅ **Endpoint de resumen** - `GET /tareas/resumen`
2. ✅ **Campo de prioridad** - `baja`, `media`, `alta`
3. ✅ **Filtro por prioridad** - `GET /tareas?prioridad=alta`
4. ✅ **Ordenamiento por fecha** - `GET /tareas?orden=asc|desc`
5. ✅ **Modelos Pydantic** - Validación automática de datos
6. ✅ **Endpoint completar todas** - `PUT /tareas/completar_todas`
7. ✅ **Documentación Swagger** - Generada automáticamente

---

## 🛠️ Estructura del Proyecto

```
TP3/
├── main.py              # Código principal de la API
│   ├── Modelos Pydantic (TareaBase, TareaCreate, TareaUpdate, Tarea)
│   ├── Gestión de BD (get_db, init_db)
│   └── Endpoints REST (CRUD + filtros + resumen)
│
├── test_TP3.py          # 27 tests automatizados
│   ├── Tests de migración a SQLite
│   ├── Tests de CRUD persistente
│   ├── Tests de búsquedas y filtros
│   └── Tests de mejoras obligatorias
│
├── requirements.txt     # Dependencias del proyecto
├── tareas.db           # Base de datos SQLite (se genera automáticamente)
└── README.md           # Este archivo
```

---

## 🐛 Solución de Problemas

### ❌ Error: "ModuleNotFoundError: No module named 'fastapi'"
**Solución:** Instala las dependencias
```bash
pip install -r requirements.txt
```

### ❌ Error: "Address already in use"
**Solución:** El puerto 8000 está ocupado. Usa otro puerto:
```bash
uvicorn main:app --reload --port 8001
```

### ❌ Los tests fallan con "Connection refused"
**Solución:** Asegúrate de que el servidor esté corriendo en otra terminal

### ❌ Error: "ENOENT: no such file or directory"
**Solución:** Estás en la carpeta incorrecta. Navega a la carpeta `TP3`:
```bash
cd ruta/a/tu/carpeta/TP3
```

---

## 📝 Ejemplos de Uso Completos

### Flujo de trabajo típico:

```bash
# 1. Crear una tarea urgente
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Entregar TP3","estado":"pendiente","prioridad":"alta"}'

# 2. Listar tareas pendientes de alta prioridad
curl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta"

# 3. Actualizar el estado a en_progreso
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado":"en_progreso"}'

# 4. Ver resumen de tareas
curl http://localhost:8000/tareas/resumen

# 5. Marcar todas como completadas
curl -X PUT http://localhost:8000/tareas/completar_todas

# 6. Verificar que todas están completadas
curl http://localhost:8000/tareas
```

---

## 👨‍💻 Información del Proyecto

- **Asignatura:** Programación
- **Trabajo Práctico:** TP3 - API de Tareas Persistente
- **Tecnologías:** FastAPI, SQLite, Pydantic, Pytest
- **Fecha de Entrega:** 17 de Octubre de 2025 - 21:00hs

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que seguiste todos los pasos de instalación
2. Asegúrate de que el servidor esté corriendo antes de ejecutar tests
3. Revisa la documentación interactiva en `/docs`
4. Consulta con tu profesor o compañeros

