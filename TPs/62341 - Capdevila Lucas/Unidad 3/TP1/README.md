# TP3.1: Introducción a FastAPI - Servidor Básico

## 📋 Descripción
Este proyecto implementa un servidor básico con FastAPI que expone endpoints simples para una Agenda de contactos, utilizando datos estáticos en memoria.

## 🚀 Instalación y Configuración

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor
```bash
uvicorn main:app --reload
```

### 3. Acceder a la aplicación
- **Servidor**: http://127.0.0.1:8000/
- **Documentación automática**: http://127.0.0.1:8000/docs
- **Contactos**: http://127.0.0.1:8000/contactos

## 📡 Endpoints Disponibles

### GET `/`
**Descripción**: Endpoint raíz que devuelve un mensaje de bienvenida.

**Respuesta**:
```json
{
  "mensaje": "Bienvenido a la Agenda de Contactos API"
}
```

### GET `/contactos`
**Descripción**: Endpoint para obtener todos los contactos de la agenda.

**Respuesta**:
```json
[
  {
    "nombre": "Juan",
    "apellido": "Pérez",
    "edad": 30,
    "teléfono": "3815551234",
    "email": "jperez@gmail.com"
  },
  {
    "nombre": "José",
    "apellido": "Gómez",
    "edad": 25,
    "teléfono": "3815551235",
    "email": "jgomez@gmail.com"
  }
  // ... más contactos
]
```

## 🧪 Ejecutar Tests

### Opción 1: Con pytest
```bash
python -m pytest test_TP1.py -v
```

### Opción 2: Ejecutar directamente
```bash
python test_TP1.py
```

**Nota**: Asegúrate de que el servidor esté corriendo antes de ejecutar los tests.

## 📁 Estructura del Proyecto

```
TP1/
├── main.py              # Servidor FastAPI principal
├── requirements.txt     # Dependencias del proyecto
├── README.md           # Este archivo
└── .gitkeep           # Archivo para mantener la carpeta en Git
```

## 🔧 Características Implementadas

- ✅ Servidor FastAPI básico
- ✅ Endpoint raíz con mensaje de bienvenida
- ✅ Endpoint `/contactos` con lista de contactos
- ✅ 12 contactos estáticos en memoria (más del mínimo requerido)
- ✅ Manejo básico de errores 404
- ✅ Documentación automática en `/docs`
- ✅ Respuestas en formato JSON
- ✅ Estructura de datos correcta para contactos

## 📊 Estructura de Contactos

Cada contacto contiene los siguientes campos:
- `nombre` (string): Nombre del contacto
- `apellido` (string): Apellido del contacto  
- `edad` (int): Edad del contacto
- `teléfono` (string): Número de teléfono
- `email` (string): Dirección de correo electrónico

## 🎯 Objetivos Cumplidos

- [x] Crear un servidor FastAPI básico
- [x] Exponer endpoint GET raíz con mensaje de bienvenida
- [x] Exponer endpoint GET para listar contactos estáticos
- [x] Mínimo 10 contactos cargados (implementados 12)
- [x] Incluir manejo básico de errores (404)
- [x] Ejecutar el servidor con uvicorn
- [x] Mostrar contactos en formato JSON

## 👨‍💻 Autor
**Lucas Capdevila** - Legajo: 62341
