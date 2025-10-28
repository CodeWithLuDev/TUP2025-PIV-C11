# TP4 - API de Proyectos y Tareas con Relaciones

**Alumno:** Gonzalo Moreno - Legajo 62490  
**Materia:** Programación IV  
**Fecha:** Octubre 2025

---

##  Descripción

Este trabajo práctico implementa una API REST que maneja **proyectos** y **tareas** con relaciones entre tablas. Cada proyecto puede tener múltiples tareas asociadas (relación 1:N).

### Lo que aprendí:
- Crear relaciones entre tablas usando claves foráneas
- Usar JOINs en consultas SQL
- Implementar CASCADE para eliminar datos relacionados
- Separar el código en módulos (models, database, main)
- Filtros avanzados combinables

---

##  Estructura del Proyecto

```
TP4/
├── main.py          # Endpoints de la API
├── models.py        # Modelos Pydantic para validación
├── database.py      # Funciones de base de datos
├── test_TP4.py      # Tests automatizados
├── tareas.db        # Base de datos SQLite
└── README.md        # Esta documentación
```

---

##  Base de Datos

### Tabla: `proyectos`
| Columna         | Tipo    | Descripción                    |
|-----------------|---------|--------------------------------|
| id              | INTEGER | Clave primaria                 |
| nombre          | TEXT    | Nombre único del proyecto      |
| descripcion     | TEXT    | Descripción opcional           |
| fecha_creacion  | TEXT    | Fecha de creación              |

### Tabla: `tareas`
| Columna         | Tipo    | Descripción                    |
|-----------------|---------|--------------------------------|
| id              | INTEGER | Clave primaria                 |
| descripcion     | TEXT    | Descripción de la tarea        |
| estado          | TEXT    | pendiente/en_progreso/completada |
| prioridad       | TEXT    | baja/media/alta                |
| proyecto_id     | INTEGER | Referencia a proyectos (FK)    |
| fecha_creacion  | TEXT    | Fecha de creación              |

**Importante:** Si eliminas un proyecto, todas sus tareas se eliminan automáticamente (CASCADE).

---

##  Cómo usar la API

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn sqlite3 pydantic pytest
```

### 2. Iniciar el servidor

```bash
uvicorn main:app --reload
```

El servidor arranca en: `http://localhost:8000`

### 3. Ver la documentación

Abrí en tu navegador:
- **Swagger UI:** http://localhost:8000/docs
- **Redoc:** http://localhost:8000/redoc

---

##  Endpoints Disponibles

###  PROYECTOS

#### Crear proyecto
```bash
POST /proyectos
Body: {
  "nombre": "Mi Proyecto",
  "descripcion": "Descripción del proyecto"
}
```

#### Listar todos los proyectos
```bash
GET /proyectos
GET /proyectos?nombre=Web    # Filtrar por nombre
```

#### Obtener un proyecto
```bash
GET /proyectos/1
# Devuelve el proyecto con cantidad de tareas
```

#### Actualizar proyecto
```bash
PUT /proyectos/1
Body: {
  "nombre": "Proyecto actualizado",
  "descripcion": "Nueva descripción"
}
```

#### Eliminar proyecto (y sus tareas)
```bash
DELETE /proyectos/1
```

---

###  TAREAS

#### Crear tarea en un proyecto
```bash
POST /proyectos/1/tareas
Body: {
  "descripcion": "Hacer la tarea",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

#### Listar tareas de un proyecto
```bash
GET /proyectos/1/tareas
```

#### Listar TODAS las tareas (con filtros)
```bash
GET /tareas
GET /tareas?estado=pendiente
GET /tareas?prioridad=alta
GET /tareas?proyecto_id=1
GET /tareas?estado=completada&prioridad=alta   # Combinar filtros
GET /tareas?orden=desc                          # Ordenar por fecha
```

#### Actualizar tarea (puede cambiar de proyecto)
```bash
PUT /tareas/1
Body: {
  "descripcion": "Tarea modificada",
  "estado": "completada",
  "proyecto_id": 2    # Mover a otro proyecto
}
```

#### Eliminar tarea
```bash
DELETE /tareas/1
```

---

###  RESÚMENES

#### Resumen de un proyecto
```bash
GET /proyectos/1/resumen
```

**Respuesta:**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Mi Proyecto",
  "total_tareas": 5,
  "por_estado": {
    "pendiente": 2,
    "en_progreso": 1,
    "completada": 2
  },
  "por_prioridad": {
    "baja": 1,
    "media": 2,
    "alta": 2
  }
}
```

#### Resumen general
```bash
GET /resumen
```

**Respuesta:**
```json
{
  "total_proyectos": 3,
  "total_tareas": 15,
  "tareas_por_estado": {
    "pendiente": 5,
    "en_progreso": 4,
    "completada": 6
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Principal",
    "cantidad_tareas": 10
  }
}
```

---

##  Ejecutar Tests

```bash
# Todos los tests
pytest test_TP4.py -v

# Un test específico
pytest test_TP4.py::test_2_1_crear_proyecto_exitoso -v
```

**Resultado:** ✅ 38 tests pasando

---

##  Relaciones entre Tablas

### ¿Cómo funciona?

1. **Crear un proyecto:**
   ```bash
   POST /proyectos → crea proyecto con ID=1
   ```

2. **Crear tareas en ese proyecto:**
   ```bash
   POST /proyectos/1/tareas → tarea.proyecto_id = 1
   POST /proyectos/1/tareas → tarea.proyecto_id = 1
   ```

3. **Si eliminas el proyecto:**
   ```bash
   DELETE /proyectos/1 → elimina el proyecto Y todas sus tareas
   ```

Esto es gracias a `ON DELETE CASCADE` en la clave foránea.

---

##  Ejemplos de Uso

### Ejemplo 1: Crear proyecto con tareas

```bash
# 1. Crear proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Sitio Web", "descripcion": "Proyecto de la facultad"}'

# Respuesta: {"id": 1, "nombre": "Sitio Web", ...}

# 2. Agregar tareas
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar homepage", "prioridad": "alta"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Crear base de datos", "prioridad": "media"}'

# 3. Ver resumen
curl http://localhost:8000/proyectos/1/resumen
```

### Ejemplo 2: Mover tarea a otro proyecto

```bash
# Crear segundo proyecto
curl -X POST http://localhost:8000/proyectos \
  -d '{"nombre": "Proyecto B"}'

# Mover la tarea 1 al proyecto 2
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'
```

---

##  Validaciones

La API valida automáticamente:
- ✅ Nombre de proyecto no vacío y único
- ✅ Descripción de tarea no vacía
- ✅ Estados válidos: `pendiente`, `en_progreso`, `completada`
- ✅ Prioridades válidas: `baja`, `media`, `alta`
- ✅ Proyecto debe existir al crear tarea
- ❌ Error 404 si proyecto/tarea no existe
- ❌ Error 409 si nombre de proyecto duplicado
- ❌ Error 400 si datos inválidos

---

##  Tecnologías Usadas

- **FastAPI** - Framework web
- **SQLite** - Base de datos
- **Pydantic** - Validación de datos
- **Pytest** - Tests automatizados
- **Uvicorn** - Servidor ASGI

---

##  Lo que me costó / Lo que aprendí

### Desafíos:
- Entender cómo funcionan las claves foráneas con CASCADE
- Hacer consultas con JOINs para contar tareas
- Separar el código en módulos sin romper los imports

### Lo que aprendí:
- A relacionar tablas usando SQL
- A hacer filtros combinables en una API
- A organizar mejor el código
- Que SQLite es muy útil para proyectos pequeños

---

##  Autor

**Gonzalo Moreno**  
Legajo: 62490  
UTN FRT - Programación IV  
Octubre 2025