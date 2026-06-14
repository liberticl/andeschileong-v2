# API Docs — Mediciones (IoT)

Documentación de los endpoints del sistema de conteo de tránsito.

**Base URL:** `https://andeschileong.cl`

**Autenticación:** JWT Bearer token (obtenido vía registro).

---

## 1. Registrar Dispositivo

Registra un dispositivo nuevo o retorna el existente. No requiere autenticación.

```
POST /api/trafico/register/
```

### Request Body (JSON)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `fingerprint` | string | Sí | Hash SHA-256 del fingerprint del navegador (64 hex chars) |
| `user_agent` | string | No | String User-Agent del navegador |
| `coords` | string | No | Coordenadas GPS `"lat,lng"` a 5 decimales (ej: `"-33.05896,-71.61998"`) |

### Respuesta 200 OK

```json
{
    "status": true,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "device_name": "Providencia, Región Metropolitana",
    "device_id": 3,
    "created": true
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `token` | string | Token JWT para autenticar requests posteriores |
| `device_name` | string | Nombre legible (generado por reverse geocoding o User-Agent) |
| `device_id` | int | ID del dispositivo en la BD |
| `created` | bool | `true` si se creó, `false` si ya existía |

### Respuesta 400 Bad Request

```json
{
    "status": false,
    "errors": {
        "fingerprint": ["Este campo es obligatorio."]
    }
}
```

### Notas

- Si el dispositivo ya existe (mismo `fingerprint`), se actualiza `last_seen` y se retorna el token existente.
- Si se envían `coords`, el nombre se genera por reverse geocoding (Nominatim).
- Si no hay coords, el nombre se genera del User-Agent (ej: `"Chrome 120 / Linux"`).

### Ejemplo curl

```bash
curl -X POST https://andeschileong.cl/api/trafico/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "fingerprint": "a1b2c3d4e5f6...",
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0",
    "coords": "-33.05896,-71.61998"
  }'
```

---

## 2. Renombrar Dispositivo

Actualiza el nombre legible de un dispositivo. Requiere JWT.

```
PATCH /api/trafico/device/
```

### Headers

| Header | Valor |
|---|---|
| `Authorization` | `Bearer <token>` |
| `Content-Type` | `application/json` |

### Request Body (JSON)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | string | Sí | Nuevo nombre del dispositivo (max 200 chars) |

### Respuesta 200 OK

```json
{
    "status": true,
    "device_name": "Contador Av. Apoquindo 3400"
}
```

### Respuesta 400 Bad Request

```json
{
    "status": false,
    "errors": {
        "name": ["Este campo es obligatorio."]
    }
}
```

### Respuesta 403 Forbidden

```json
{
    "status": false,
    "errors": {
        "inactive": ["El dispositivo no está activo"]
    }
}
```

### Respuesta 401 Unauthorized

```json
{
    "detail": "Token inválido"
}
```

### Ejemplo curl

```bash
curl -X PATCH https://andeschileong.cl/api/trafico/device/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{"name": "Contador Av. Apoquindo 3400"}'
```

---

## 3. Enviar Conteo de Tránsito

Registra una medición de tránsito. Requiere JWT.

```
POST /api/trafico/
```

### Headers

| Header | Valor |
|---|---|
| `Authorization` | `Bearer <token>` |
| `Content-Type` | `application/json` |

### Request Body (JSON)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `datetime` | string (ISO 8601) | Sí | Fecha/hora de la medición (ej: `"2026-06-14T15:30:00-04:00"`) |
| `car_count` | int | No | Cantidad de autos (default: 0) |
| `person_count` | int | No | Cantidad de peatones (default: 0) |
| `bicycle_count` | int | No | Cantidad de bicicletas (default: 0) |
| `motorcycle_count` | int | No | Cantidad de motos (default: 0) |
| `truck_count` | int | No | Cantidad de camiones (default: 0) |
| `bus_count` | int | No | Cantidad de buses (default: 0) |
| `skater_count` | int | No | Cantidad de patinetas (default: 0) |
| `pet_count` | int | No | Cantidad de mascotas (default: 0) |

**Validación:** Al menos un campo de conteo debe ser mayor a 0.

### Respuesta 201 Created

```json
{
    "status": true,
    "data": {
        "datetime": "2026-06-14T15:30:00-04:00",
        "car_count": 5,
        "person_count": 12,
        "bicycle_count": 3,
        "motorcycle_count": 1,
        "truck_count": 0,
        "bus_count": 2,
        "skater_count": 0,
        "pet_count": 1
    }
}
```

### Respuesta 400 Bad Request

```json
{
    "status": false,
    "errors": {
        "datetime": ["Este campo es obligatorio."],
        "count": ["Al menos un campo debe ser mayor a cero."],
        "fields": ["car_count", "person_count", "bicycle_count", "motorcycle_count", "truck_count", "bus_count", "skater_count", "pet_count"]
    }
}
```

### Respuesta 403 Forbidden

```json
{
    "status": false,
    "errors": {
        "inactive": ["El dispositivo no está activo"]
    }
}
```

### Respuesta 401 Unauthorized

```json
{
    "detail": "Token inválido"
}
```

### Notas

- El `last_seen` del dispositivo se actualiza automáticamente en cada POST exitoso.
- El `created_datetime` se genera automáticamente en el servidor.

### Ejemplo curl

```bash
curl -X POST https://andeschileong.cl/api/trafico/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "datetime": "2026-06-14T15:30:00-04:00",
    "car_count": 5,
    "person_count": 12,
    "bicycle_count": 3,
    "motorcycle_count": 1,
    "bus_count": 2,
    "pet_count": 1
  }'
```

---

## 4. Descargar Modelo ONNX

Sirve el modelo YOLO26n para uso en el navegador.

```
GET /apps/mediciones/contador/model/
```

### Query Parameters

| Parámetro | Opciones | Default | Descripción |
|---|---|---|---|
| `size` | `320`, `640` | `640` | Tamaño de input del modelo |

### Respuesta 200 OK

- Content-Type: `application/octet-stream`
- Body: Archivo ONNX binario (~9.5MB para 640px, ~9.8MB para 320px)

### Notas

- `size=320`: Para dispositivos con RAM ≤ 2GB (Raspberry Pi 3, celulares viejos)
- `size=640`: Para dispositivos con RAM > 2GB (computadores normales, Raspberry Pi 4/5)

### Ejemplo curl

```bash
# Modelo 640px (default)
curl -O https://andeschileong.cl/apps/mediciones/contador/model/

# Modelo 320px (baja RAM)
curl -O "https://andeschileong.cl/apps/mediciones/contador/model/?size=320"
```

---

## Autenticación JWT

### Estructura del Token

El token JWT contiene:

```json
{
    "devicename": "nombre del dispositivo",
    "devicecoords": "-33.05896,-71.61998",
    "fingerprint": "hash SHA-256 del navegador"
}
```

### Obtener Token

El token se obtiene al registrar el dispositivo (`POST /api/trafico/register/`). Se guarda en `localStorage` del navegador y se envía en cada request como `Authorization: Bearer <token>`.

### Errores de Auth

| HTTP Status | Mensaje | Causa |
|---|---|---|
| 401 | `Token inválido` | Token corrupto o mal formado |
| 401 | `El token ha expirado` | Token expirado |
| 401 | `Dispositivo no encontrado` | El device fue eliminado de la BD |
| 403 | `El dispositivo no está activo` | `is_active = False` en la BD |
