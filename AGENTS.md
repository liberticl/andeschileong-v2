# AGENTS.md - Contexto del Proyecto AndesChileOng / Ciudades Pendientes V2

> **INSTRUCCIÓN OBLIGATORIA:** Cada vez que se realice una modificación al proyecto (nuevos modelos, vistas, apps, cambios de config, etc.), este archivo DEBE actualizarse para reflejar el estado actual del código. Si se agrega una nueva app, se modifica un modelo, se cambia una URL, o se altera la arquitectura, actualizar la sección correspondiente aquí.

---

## 1. Resumen

ONG **Andes Chile** → organización sin fines de lucro dedicada a la movilidad ciclista urbana en Chile y Argentina.

Plataforma web **"Ciudades Pendientes V2"** que permite la visualización inmersiva de datos de movilidad (uso de Strava, flujos ciclistas) mediante mapas interactivos con DeckGL/Pydeck.

Base URL: `https://andeschileong.cl`
Dominio estático (Hugo): `https://andeschileong.cl`

---

## 2. Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Django 4.2, Django REST Framework 3.16 |
| Frontend (app) | Pydeck 0.9.1, DeckGL 8.9.*, Leaflet, Bootstrap 5 |
| Sitio estático | Hugo Extended 0.121.2, tema hugo-sustain |
| BD relacional | PostgreSQL (psycopg2-binary) |
| BD documental | MongoDB (pymongo 4.3) |
| Geo/espacial | GeoPandas, Shapely, PyProj, Fiona |
| Auth IoT | PyJWT 2.10 |
| Contenedorización | Docker, Docker Compose, Nginx, Gunicorn |
| Python | 3.11+ (`.python-version`: 3.11) |

---

## 3. Arquitectura de Apps Django

| App | Función | Ubicación |
|---|---|---|
| `ciudadespendientes` | Core del sistema: modelos Zone/StravaData, visualización de mapas interactivos, carga de datos Strava, clasificación de flujos | `ciudadespendientes/` |
| `accounts` | Sistema de autenticación custom: Account (custom user), Organization, Permission | `accounts/` |
| `measuring` | API IoT para dispositivos de conteo de tráfico: Device, TrafficCount | `measuring/` |
| `hugo_edit` | CMS para el sitio Hugo: CRUD de Actividades → genera .md → rebuild Hugo | `hugo_edit/` |
| `licitaciones` | Dashboard de licitaciones de infraestructura ciclista desde Mercado Público | `licitaciones/` |

---

## 4. hugo_site (Sitio Principal Andes Chile ONG)

El sitio público de la ONG, generado con Hugo.

- **Tema:** hugo-sustain (customizado extensivamente)
- **Config:** `hugo_site/config.toml`
- **buildFuture:** `true` (incluye contenido con fechas futuras)
- **Google Analytics:** `G-LQG5PZVGT6`

### Secciones de contenido

| Sección | Ruta | Descripción | Gestión |
|---|---|---|---|
| Inicio | `content/_index.md` | Página principal | Manual |
| Actividades | `content/actividades/` | 51+ posts (2017-2026): cicletadas, refugios, foros, talleres | **hugo_edit** (Django) |
| Noticias | `content/noticias/` | 16 artículos de prensa y comunicados | Manual |
| Estudios | `content/estudios/` | Investigaciones (INGELECTRA, Encuesta Uso Bici) | Manual |
| Nosotros | `content/nosotros/` | Sobre la organización | Manual |
| Registro | `content/registro/` | Registro de locales ciclamigables | Manual |
| Cicletada | `content/cicletada/` | Redirect a tracking GPS en vivo | Manual |

### Layouts y Shortcodes customizados

**Layouts** (`hugo_site/layouts/`):
- `_default/baseof.html` - Base con GA, Bootstrap 5, Font Awesome
- `_default/single.html` - Página individual
- `_default/list.html` - Listado simple
- `_default/actividades.html` - Grid de actividades
- `_default/estudios.html` - Grid de estudios
- `_default/nosotros.html` - About us
- `partials/header.html` - Navbar responsive
- `partials/footer.html` - Footer
- `partials/social.html` - Links redes sociales
- `partials/actividad.html` - Modal Desafío Araucanía
- `partials/foro-nacional.html` - Modal Foro Nacional
- `partials/refugiociclista.html` - Modal Refugio Ciclista
- `partials/listado-activities.html` - Card de actividad con animación pulse

**Shortcodes:**
- `button` - Botón con enlace
- `color-bar` - Barra de color
- `download` - Botón de descarga
- `form` - Embed de Google Forms
- `gallery` - Galería de imágenes con modal
- `google-video` - Embed de Google Drive
- `minitext` - Bloques de texto predefinidos
- `pdf` - Embed de PDFs
- `videogallery` - Galería de videos

### Assets estáticos

- `static/img/` - Imágenes organizadas por año y sección
- `static/docs/` - Documentos PDF (papers, presentaciones)
- `assets/css/main.css` - CSS custom (esquema azul #2241a8)

---

## 5. hugo_edit ↔ hugo_site (Flujo de Sincronización)

```
hugo_edit (Django)  ──→  hugo_site/content/actividades/{year}/{slug}.md  ──→  Hugo build  ──→  public/
```

### Modelo Activity (`hugo_edit/models.py`)

| Campo | Tipo | Descripción |
|---|---|---|
| `title` | CharField(200) | Título de la actividad |
| `description` | TextField | Resumen/bajada |
| `date` | DateField | Fecha (requerido) |
| `featured_image` | CharField(255) | Ruta a imagen destacada (ej: `/img/fotos/mi-foto.jpg`) |
| `tags` | CharField(255) | Tags separados por comas |
| `content` | TextField | Cuerpo en Markdown |

### Flujo de guardado

1. `Activity.save()` → `super().save()` → `self.generate_markdown()`
2. `generate_markdown()` escribe `.md` en `hugo_site/content/actividades/{year}/{slug}.md`
3. Ejecuta `subprocess.run(['hugo', '--minify'])` para reconstruir

### Flujo de eliminación

1. `Activity.delete()` → elimina `.md` si existe → `subprocess.run(['hugo', '--minify'])`
2. `super().delete()` para eliminar de la DB

### Comando de recuperación

```bash
python manage.py sync_hugo
```
Regenera TODOS los `.md` desde la DB y reconstruye Hugo. Usar si los archivos se pierden o desincronizan.

### Intranet (solo superuser)

- `/intranet/` → Dashboard
- `/intranet/actividades/` → Listado de actividades
- `/intranet/actividades/add/` → Crear actividad
- `/intranet/actividades/<pk>/edit/` → Editar
- `/intranet/actividades/<pk>/delete/` → Eliminar

Editor Markdown: SimpleMDE (CDN) en el campo `content`.

### Nota importante

`hugo_edit` **solo gestiona la sección `actividades/`**. Las demás secciones (noticias, estudios, nosotros, etc.) se editan directamente como archivos `.md` en `hugo_site/content/`.

---

## 6. Bases de Datos

### PostgreSQL (modelos relacionales)

| Modelo | App | Descripción |
|---|---|---|
| `Zone` | ciudadespendientes | Zonas geográficas (país, comuna, regional, particular) con OSM ID y coordenadas |
| `StravaData` | ciudadespendientes | Colecciones de datos Strava por zona/año/mes, flag `on_mongo` |
| `GeoRegionBoundary` | ciudadespendientes | Límites geográficos de comunas chilenas (polígonos GeoJSON en BD local) |
| `Account` | accounts | Custom user (email = username), zonas, permisos, organizaciones |
| `Organization` | accounts | Organizaciones adscritas a la plataforma |
| `Permission` | accounts | Permisos granulares (ej: `view_strava_data`) |
| `Device` | mediciones | Dispositivos IoT: fingerprint (SHA-256), nombre legible, token JWT, coordenadas (5 dec), user_agent, last_seen |
| `TrafficCount` | mediciones | Registros de conteo vehicular: car, person, bicycle, motorcycle, truck, bus, skater, pet_count |
| `Activity` | hugo_edit | Actividades del sitio Hugo |
| `Licitacion` | licitaciones | Licitaciones de infraestructura ciclista/peatonal de Mercado Público |
| `SyncLog` | licitaciones | Logs de sincronización con API de Mercado Público |

### MongoDB (trazas espaciales)

- **Database:** `ciudadespendientes` (configurable via `MONGO_CP_DB`)
- **Collection:** `strava` (configurable via `CP_STRAVA_COLLECTION`)
- **Documentos:** trazas de viajes de Strava con `geometry.coordinates`, `total_trip_count`, `middlePoint` (GeoJSON Point), `year`
- **Índice geoespacial:** `middlePoint` para consultas `$geoIntersects`

### Pipelines de agregación (`ciudadespendientes/mongodb.py`)

- `middle_points_aggregate` - Calcula punto medio de cada traza
- `points_inside` - Filtra trazas dentro de polígonos de ciudades por año
- `points_inside_2` - Variante alternativa con `osmId`
- `map_middle_point` - Punto medio de toda una ciudad

---

## 7. Modelos Clave y Relaciones

```
Organization ──M2M──→ Account ──M2M──→ Zone
                          │                 │
                          │                 └── StravaData (sector FK → Zone)
                          │                       └── get_polygon() → GeoRegionBoundary (local) → OSM (fallback)
                          │
Permission ──M2M──→ Account
                          │
Device (JWT auth) ──FK──→ TrafficCount
                          │
Activity (independiente) ──genera──→ .md en hugo_site/
```

### Cuenta custom (AUTH_USER_MODEL)

```python
AUTH_USER_MODEL = "accounts.Account"
```

El email es el campo de usuario (`USERNAME_FIELD = "email"`).

---

## 8. Variables de Entorno (`.env`)

```env
# MongoDB
MONGO_DB="mongodb://..."
MONGO_CP_DB="ciudadespendientes"
CP_STRAVA_COLLECTION="strava"

# PostgreSQL
DB_HOST="..."
DB_PORT="..."
DB_NAME="ciudadespendientes"
DB_USER="postgres"
DB_PASS="..."

# Seguridad
CP_JWT_SECRET="..."       # Secret para tokens JWT de dispositivos IoT
SECRET_KEY="..."          # Django secret key

# Mercado Público
MERCADO_PUBLICO_TICKET="..."

# Config
DECKGL_VERSION="8.9.*"
DATA_DIR="ciudadespendientes/data"
DEBUG="true"
ENV="prod"
```

---

## 9. URLs Principales

| Ruta | Vista | App | Descripción |
|---|---|---|---|
| `/login/` | `CustomLoginView` | accounts | Login |
| `/logout/` | `LogoutView` | accounts | Logout |
| `/apps/` | `welcome` | ciudadespendientes | Dashboard principal |
| `/apps/ciudadespendientes/` | `find` | ciudadespendientes | Búsqueda de datos |
| `/apps/ciudadespendientes/mapa/` | `show_data` | ciudadespendientes | Mapa interactivo DeckGL |
| `/intranet/` | `intranet_dashboard` | hugo_edit | CMS Hugo (superuser) |
| `/intranet/actividades/` | CRUD views | hugo_edit | Gestionar actividades |
| `/admin/` | Django admin | - | Admin general |
| `/apps/mediciones/contador/` | `contador` | mediciones | Contador de tránsito (ONNX + YOLO26n) |
| `/apps/mediciones/contador/model/` | `contador_model` | mediciones | Modelo ONNX (320/640px según RAM) |
| `/api/trafico/` | `TrafficCountAPIView` | mediciones | API IoT (JWT auth) |
| `/api/trafico/register/` | `DeviceRegisterView` | mediciones | Auto-registro de dispositivos (sin auth) |
| `/api/trafico/device/` | `DeviceNameUpdateView` | mediciones | Renombrar dispositivo (JWT auth) |
| `/apps/licitaciones/` | `dashboard` | licitaciones | Dashboard licitaciones ciclistas |
| `/apps/licitaciones/lista/` | `licitaciones_list` | licitaciones | Listado de licitaciones |
| `/apps/licitaciones/<codigo>/` | `licitacion_detalle` | licitaciones | Detalle de licitación |
| `/apps/licitaciones/api/stats/` | `api_stats` | licitaciones | API JSON para charts |

---

## 10. Docker

### Levantar

```bash
docker-compose up --build -d
```

### Estructura del Dockerfile

1. `python:3.11-slim` como base
2. Instala dependencias de Python
3. Instala Nginx + Hugo 0.121.2
4. Compila Hugo (`hugo --minify`)
5. Recolecta estáticos Django
6. CMD: `sync_hugo` → Nginx → Gunicorn (puerto 8000, expuesto vía Nginx en puerto 80)

### Servicios

| Servicio | Puerto | Descripción |
|---|---|---|
| web | 80 (host) → 8000 (interno) | Django + Nginx + Gunicorn |

---

## 11. Comandos Útiles

```bash
# Migraciones
python manage.py migrate
python manage.py createsuperuser

# Estáticos
python manage.py collectstatic

# Sincronizar Hugo
python manage.py sync_hugo

# Sincronizar licitaciones de Mercado Público
python manage.py sync_licitaciones --dias 7
python manage.py sync_licitaciones --dias 30 --ticket TU_TICKET

# Descargar límites geográficos de Chile (comunas)
# Solo necesario en primera instalación o para actualizar datos geográficos
python manage.py download_chile_boundaries --source github
python manage.py download_chile_boundaries --source github --clear  # Reemplazar todos

# Desarrollo
python manage.py runserver

# Docker
docker-compose up --build -d
docker-compose exec django python manage.py <comando>
docker-compose logs -f
```

---

## 12. Archivos Importantes

| Archivo | Propósito |
|---|---|
| `andeschileong/settings.py` | Configuración principal (DBs, apps, Hugo, colores capas) |
| `andeschileong/urls.py` | URL routing principal |
| `ciudadespendientes/models.py` | Zone, StravaData, GeoRegionBoundary |
| `ciudadespendientes/views.py` | show_data, color_ride_map, welcome, find |
| `ciudadespendientes/utils.py` | Funciones geo, MongoDB, DeckGL HTML |
| `ciudadespendientes/mongodb.py` | Pipelines de agregación MongoDB |
| `ciudadespendientes/classifier.py` | Clasificación de flujos (SECTRA, general) |
| `ciudadespendientes/choices.py` | Constantes: regiones, países, meses, años |
| `ciudadespendientes/admin.py` | Admin con upload ZIP a MongoDB |
| `ciudadespendientes/external_apis.py` | Geocodificación (local first → OSM fallback), reverse geocoding, parse User-Agent |
| `ciudadespendientes/management/commands/download_chile_boundaries.py` | Descarga polígonos comunas Chile |
| `accounts/models.py` | Account, Organization, Permission |
| `apps/mediciones/models.py` | Device, TrafficCount |
| `apps/mediciones/views.py` | API IoT TrafficCountAPIView, DeviceRegisterView, DeviceNameUpdateView |
| `apps/mediciones/templates/mediciones/contador.html` | Aplicación de detección YOLO26n + ONNX (fingerprint, reverse geocoding, sync) |
| `hugo_edit/models.py` | Activity (genera .md y rebuild Hugo) |
| `hugo_edit/management/commands/sync_hugo.py` | Comando sync DB → Hugo |
| `hugo_edit/admin.py` | Admin custom con SimpleMDE |
| `licitaciones/models.py` | Licitacion, SyncLog |
| `licitaciones/views.py` | Dashboard, listado, detalle, api_stats |
| `licitaciones/urls.py` | URLs de licitaciones |
| `licitaciones/admin.py` | Admin con filtros y acciones |
| `licitaciones/forms.py` | Formulario de filtros (FiltroLicitacionesForm con comuna, región, año, estado) |
| `licitaciones/management/commands/sync_licitaciones.py` | Sync con API Mercado Público |
| `licitaciones/templates/licitaciones/` | Templates del dashboard |
| `hugo_site/config.toml` | Configuración de Hugo |
| `hugo_site/layouts/` | Layouts y partials customizados |
| `hugo_site/content/` | Contenido Markdown del sitio |
| `hugo_site/assets/css/main.css` | CSS custom del sitio |
| `templates/` | Templates Django (base, navbar, 404, 403) |
| `Dockerfile` | Configuración de Docker |
| `docker-compose.yml` | Orquestación Docker |
| `requirements.txt` | Dependencias Python |
| `.env` | Variables de entorno |
| `docs/api.md` | Documentación de API para endpoints de tránsito |
| `docs/guia-dispositivos.md` | Guía completa para dispositivos de conteo (no-técnica + técnica) |

---

## 13. Constantes de Configuración

### Capas de colores (DeckGL)

```python
LAYERS = {
    'green':  {'color': '[0, 128, 0, 150]',   'width': 3, 'label': 'Flujo bajo'},
    'orange': {'color': '[255, 165, 0, 190]', 'width': 5, 'label': 'Flujo medio'},
    'red':    {'color': '[255, 0, 0, 210]',   'width': 5, 'label': 'Flujo alto'}
}
```

### Años disponibles

```python
ALLOWED_YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
```

### Zonas (choices.py)

- **Tipos:** País, Comuna, Zona Regional, Particular
- **Países:** Chile, Argentina
- **Meses:** Enero-Diciembre + "Todo el año"
- **Regiones Chile:** Arica y Parinacota → Magallanes (16 regiones)
- **Regiones Argentina:** Buenos Aires, Tucumán, Santa Fe
