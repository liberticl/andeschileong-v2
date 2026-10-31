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
| `car_count` | int | No | Cantidad de autos (default: 0). Siempre el **total** |
| `person_count` | int | No | Cantidad de peatones (default: 0) |
| `bicycle_count` | int | No | Cantidad de bicicletas (default: 0) |
| `motorcycle_count` | int | No | Cantidad de motos (default: 0) |
| `truck_count` | int | No | Cantidad de camiones (default: 0) |
| `bus_count` | int | No | Cantidad de buses (default: 0) |
| `skater_count` | int | No | Cantidad de patinetas (default: 0) |
| `pet_count` | int | No | Cantidad de mascotas (default: 0) |
| `line` | object \| null | No | Línea de conteo normalizada 0-1: `{x1,y1,x2,y2}`. `A` = start `(x1,y1)`, `B` = end `(x2,y2)`. `null`/ausente = conteo por aparición (sin dirección) |
| `direction_counts` | object | No | Desglose direccional: `{a_to_b: {...}, b_to_a: {...}}` con claves `*_count` (o cortas `car/person/bicycle/...`) |
| `side_a_name` | string | No | Nombre de referencia del lado A, máx 100 (ej: `"Norte"`). Se edita en ⚙️ del contador, sale en overlay/CSV |
| `side_b_name` | string | No | Nombre de referencia del lado B, máx 100 (ej: `"Sur"`) |
| `side_names` | object | No | Alternativa anidada: `{a, b}` (equivale a `side_a_name`/`side_b_name`) |

**Validación:**
- Al menos un campo de conteo debe ser mayor a 0 (entre totales y direccionales).
- 100% backward-compatible: un body solo con totales funciona igual que antes.
- Si se envía `direction_counts` con suma > 0 para una categoría, el total debe ser igual a `a_to_b + b_to_a` (o puede omitirse el total: el servidor lo deriva).
- Si se envía `direction_counts` con datos, `line` es obligatoria (los cruces solo son interpretables contra su línea).
- `line: null` (o ausente) = conteo por aparición: cuenta objetos nuevos sin distinguir dirección (requiere 3 cuadros estables, sin línea dibujada).

**Convención A/B:** ver `docs/guia-dispositivos.md` §7. Resumen: `signedDistance = (end−start) × (point−start)` sobre el footPoint; `< −12px` = lado A (−1), `> +12px` = lado B (+1). `A→B` = cruce −1 → +1, `B→A` = +1 → −1. En el overlay se etiquetan los **lados** (`A` en la mitad del lado −1, `B` en la del lado +1); los vértices start/end solo llevan puntos rojos.

### Respuesta 201 Created

```json
{
    "status": true,
    "data": {
        "datetime": "2026-06-14T15:30:00-04:00",
        "created_datetime": "2026-06-14T15:32:10.123456-04:00",
        "car_count": 5,
        "person_count": 12,
        "bicycle_count": 3,
        "motorcycle_count": 1,
        "truck_count": 0,
        "bus_count": 2,
        "skater_count": 0,
        "pet_count": 1,
        "line": null,
        "direction_counts": {
            "a_to_b": {
                "car_count": 0, "person_count": 0, "bicycle_count": 0,
                "motorcycle_count": 0, "truck_count": 0, "bus_count": 0,
                "skater_count": 0, "pet_count": 0
            },
            "b_to_a": {
                "car_count": 0, "person_count": 0, "bicycle_count": 0,
                "motorcycle_count": 0, "truck_count": 0, "bus_count": 0,
                "skater_count": 0, "pet_count": 0
            }
        }
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

Otros 400 posibles:

```json
{ "status": false, "errors": { "bicycle_count": ["Total (5) ≠ A→B (3) + B→A (1)."] } }
{ "status": false, "errors": { "line": ["La línea (x1,y1,x2,y2) es requerida cuando se envía direction_counts."] } }
{ "status": false, "errors": { "line": ["Línea incompleta: se requieren x1,y1,x2,y2 o null."] } }
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
- El `created_datetime` se genera automáticamente en el servidor al recibir el dato (hora de recepción, no editable por el cliente; se devuelve en la respuesta 201).

### Ejemplo curl (sin dirección, backward-compatible)

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

### Ejemplo curl (con dirección: bicycle 3 A→B + 1 B→A)

```bash
curl -X POST https://andeschileong.cl/api/trafico/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "datetime": "2026-10-31T12:00:00-04:00",
    "bicycle_count": 4,
    "line": {"x1": 0.2, "y1": 0.6, "x2": 0.8, "y2": 0.6},
    "side_names": {"a": "Norte", "b": "Sur"},
    "direction_counts": {
      "a_to_b": {"bicycle_count": 3},
      "b_to_a": {"bicycle_count": 1}
    }
  }'
```

Respuesta 201 (extracto):

```json
{
    "status": true,
    "data": {
        "datetime": "2026-10-31T12:00:00-04:00",
        "created_datetime": "2026-10-31T12:02:10.123456-04:00",
        "bicycle_count": 4,
        "line": {"x1": 0.2, "y1": 0.6, "x2": 0.8, "y2": 0.6},
        "side_names": {"a": "Norte", "b": "Sur"},
        "direction_counts": {
            "a_to_b": {"bicycle_count": 3, "car_count": 0, "...": 0},
            "b_to_a": {"bicycle_count": 1, "car_count": 0, "...": 0}
        }
    }
}
```

Forma alternativa (campos planos, equivalente): `line_x1,line_y1,line_x2,line_y2` + `bicycle_a_to_b: 3, bicycle_b_to_a: 1`. Si se omite `bicycle_count`, el servidor lo deriva (`3 + 1 = 4`).

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
