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
| `hugo_edit` | CMS para el sitio Hugo: CRUD de Actividades/Noticias/Estudios → genera .md → rebuild Hugo via Celery. Gestión de borradores, soft delete, papelera | `hugo_edit/` |
| `licitaciones` | Dashboard de licitaciones de infraestructura ciclista desde Mercado Público | `licitaciones/` |

---

## 4. hugo_site (Sitio Principal Andes Chile ONG)

El sitio público de la ONG, generado con Hugo.

- **Tema:** hugo-sustain (customizado extensivamente)
- **Config:** `hugo_site/config.toml`
- **buildFuture:** `true` (incluye contenido con fechas futuras)
- **buildDrafts:** `false` (oculta borradores en sitio público)
- **Google Analytics:** `G-LQG5PZVGT6`

### Secciones de contenido

| Sección | Ruta | Descripción | Gestión |
|---|---|---|---|
| Inicio | `content/_index.md` | Página principal | Manual |
| Actividades | `content/actividades/` | 55 posts (2017-2026): cicletadas, refugios, foros, talleres | **hugo_edit** (Django) |
| Noticias | `content/noticias/` | 15 artículos de prensa y comunicados | **hugo_edit** (Django) |
| Estudios | `content/estudios/` | 2 investigaciones (INGELECTRA, Encuesta Uso Bici) | **hugo_edit** (Django) |
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

### Templates Hugo (para intranet)

- `hugo_site/layouts/_default/noticias.html` - Timeline layout para /noticias/
- `hugo_site/layouts/_default/estudios.html` - Grid layout para /estudios/
- `hugo_site/layouts/partials/listado-noticias.html` - Timeline item (sin tags, sin puntos en años)
- `hugo_site/layouts/partials/listado-estudios.html` - Card con imagen opcional, `small.text-muted` fecha
- `hugo_site/layouts/partials/listado-actividades.html` - Card existente

---

## 5. hugo_edit ↔ hugo_site (Flujo de Sincronización)

```
hugo_edit (Django)  ──→  hugo_site/content/{section}/{year}/{slug}.md  ──→  Celery task (rebuild_hugo)  ──→  public/
```

### Modelos (`hugo_edit/models.py`)

#### Activity

| Campo | Tipo | Descripción |
|---|---|---|
| `title` | CharField(200) | Título de la actividad |
| `description` | TextField | Resumen/bajada |
| `date` | DateField | Fecha (requerido) |
| `featured_image` | CharField(255) | Ruta a imagen destacada (ej: `/img/fotos/mi-foto.jpg`) |
| `tags` | CharField(255) | Tags separados por comas |
| `is_published` | BooleanField | Publicado (default=False) |
| `is_deleted` | BooleanField | Soft delete (default=False) |
| `content` | TextField | Cuerpo en Markdown |

#### Noticia

| Campo | Tipo | Descripción |
|---|---|---|
| `title` | CharField(200) | Título de la noticia |
| `description` | TextField | Resumen/bajada (opcional) |
| `date` | DateField | Fecha |
| `tags` | CharField(255) | Tags separados por comas |
| `is_published` | BooleanField | Publicado (default=False) |
| `is_deleted` | BooleanField | Soft delete (default=False) |
| `content` | TextField | Cuerpo en Markdown |

#### Estudio

| Campo | Tipo | Descripción |
|---|---|---|
| `title` | CharField(200) | Título del estudio |
| `description` | TextField | Resumen/bajada (opcional) |
| `date` | DateField | Fecha |
| `featured_image` | CharField(255) | Ruta a imagen destacada |
| `is_published` | BooleanField | Publicado (default=False) |
| `is_deleted` | BooleanField | Soft delete (default=False) |
| `content` | TextField | Cuerpo en Markdown |

### Flujo de guardado

1. `{Model}.save()` → `super().save()` → `self.generate_markdown()`
2. `generate_markdown()` escribe `.md` en `hugo_site/content/{section}/{year}/{slug}.md`
3. `rebuild_hugo.delay()` envía tarea asincrónica a Celery para reconstruir Hugo

### Flujo de soft delete

1. `{Model}.soft_delete()` → `is_deleted = True` → `self.save()` → `self.remove_hugo_file()` → `rebuild_hugo.delay()`
2. El registro **no se elimina** de la DB, solo se oculta de la intranet
3. Se puede restaurar con `{Model}.restore()` → `is_deleted = False` → `self.save()`

### Tarea Celery (`hugo_edit/tasks.py`)

La reconstrucción de Hugo se ejecuta de forma asincrónica via Celery:
- `rebuild_hugo()` ejecuta `hugo --minify` con timeout de 60s
- Broker: Redis (`redis://redis:6379/0`)
- Auto-descubierta por `app.autodiscover_tasks()` en `andeschileong/celery.py`

### Comando de recuperación

```bash
python manage.py sync_hugo
```
Regenera TODOS los `.md` desde la DB (Actividades, Noticias, Estudios) y reconstruye Hugo. Usar si los archivos se pierden o desincronizan.

### Intranet (solo is_staff)

- `/intranet/` → Dashboard con cards de Actividades/Noticias/Estudios
- `/intranet/actividades/` → Listado de actividades (con búsqueda y paginación)
- `/intranet/actividades/add/` → Crear actividad
- `/intranet/actividades/<pk>/edit/` → Editar
- `/intranet/actividades/<pk>/delete/` → Soft delete
- `/intranet/actividades/eliminados/` → Papelera de actividades
- `/intranet/actividades/<pk>/restore/` → Restaurar actividad
- `/intranet/noticias/` → Listado de noticias (con búsqueda y paginación)
- `/intranet/noticias/add/` → Crear noticia
- `/intranet/noticias/<pk>/edit/` → Editar
- `/intranet/noticias/<pk>/delete/` → Soft delete
- `/intranet/noticias/eliminados/` → Papelera de noticias
- `/intranet/noticias/<pk>/restore/` → Restaurar noticia
- `/intranet/estudios/` → Listado de estudios (con búsqueda y paginación)
- `/intranet/estudios/add/` → Crear estudio
- `/intranet/estudios/<pk>/edit/` → Editar
- `/intranet/estudios/<pk>/delete/` → Soft delete
- `/intranet/estudios/eliminados/` → Papelera de estudios
- `/intranet/estudios/<pk>/restore/` → Restaurar estudio

Los listados incluyen:
- Búsqueda por título (`?q=`)
- Paginación (15 ítems/página)
- Botón "Ver eliminados" (solo si hay registros en papelera)
- Tags mostrados como badges individuales

### Control de acceso

- **Acceso a intranet:** `is_staff=True` en el modelo `Account`
- **Superuser:** Solo `francisco@andeschileong.cl` tiene `is_superuser=True`
- **Staff:** 9 usuarios con `@andeschileong.cl` tienen `is_staff=True`
- **Inactivos:** `katherine@andeschileong.cl` tiene `is_active=False`
- **Navbar:** Muestra enlace "INTRANET" solo si `user.is_staff`

### Nota importante

`hugo_edit` gestiona las secciones `actividades/`, `noticias/` y `estudios/` del sitio Hugo. La sección `nosotros/` y demás se editan directamente como archivos `.md` en `hugo_site/content/`.

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
| `Activity` | hugo_edit | Actividades del sitio Hugo (is_published, is_deleted) |
| `Noticia` | hugo_edit | Noticias del sitio Hugo (is_published, is_deleted) |
| `Estudio` | hugo_edit | Estudios del sitio Hugo (is_published, is_deleted) |
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
Noticia (independiente)  ──genera──→ .md en hugo_site/
Estudio (independiente)  ──genera──→ .md en hugo_site/
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

# Email (Gmail SMTP)
EMAIL_HOST_USER="contacto@andeschileong.cl"
EMAIL_HOST_PASSWORD="..."

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
| `/intranet/` | `intranet_dashboard` | hugo_edit | Dashboard CMS (solo is_staff) |
| `/intranet/actividades/` | `ActivityListView` | hugo_edit | Listado actividades |
| `/intranet/actividades/add/` | `ActivityCreateView` | hugo_edit | Crear actividad |
| `/intranet/actividades/<pk>/edit/` | `ActivityUpdateView` | hugo_edit | Editar actividad |
| `/intranet/actividades/<pk>/delete/` | `ActivityDeleteView` | hugo_edit | Soft delete actividad |
| `/intranet/actividades/eliminados/` | `ActivityDeletedView` | hugo_edit | Papelera actividades |
| `/intranet/actividades/<pk>/restore/` | `restore_activity` | hugo_edit | Restaurar actividad |
| `/intranet/noticias/` | `NoticiaListView` | hugo_edit | Listado noticias |
| `/intranet/noticias/add/` | `NoticiaCreateView` | hugo_edit | Crear noticia |
| `/intranet/noticias/<pk>/edit/` | `NoticiaUpdateView` | hugo_edit | Editar noticia |
| `/intranet/noticias/<pk>/delete/` | `NoticiaDeleteView` | hugo_edit | Soft delete noticia |
| `/intranet/noticias/eliminados/` | `NoticiaDeletedView` | hugo_edit | Papelera noticias |
| `/intranet/noticias/<pk>/restore/` | `restore_noticia` | hugo_edit | Restaurar noticia |
| `/intranet/estudios/` | `EstudioListView` | hugo_edit | Listado estudios |
| `/intranet/estudios/add/` | `EstudioCreateView` | hugo_edit | Crear estudio |
| `/intranet/estudios/<pk>/edit/` | `EstudioUpdateView` | hugo_edit | Editar estudio |
| `/intranet/estudios/<pk>/delete/` | `EstudioDeleteView` | hugo_edit | Soft delete estudio |
| `/intranet/estudios/eliminados/` | `EstudioDeletedView` | hugo_edit | Papelera estudios |
| `/intranet/estudios/<pk>/restore/` | `restore_estudio` | hugo_edit | Restaurar estudio |
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
| redis | 6379 | Redis (broker para Celery) |
| celery-worker | - | Worker de Celery (2 concurrencia) |
| celery-beat | - | Programador de tareas Celery |

---

## 11. Comandos Útiles

```bash
# Migraciones
python manage.py migrate
python manage.py createsuperuser

# Estáticos
python manage.py collectstatic

# Sincronizar Hugo (regenera .md desde la DB)
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
docker-compose exec web python manage.py <comando>
docker-compose logs -f
docker-compose restart web  # Reiniciar solo el servicio web

# Docker (comandos one-off)
docker-compose run --rm web python manage.py <comando>  # Ejecutar sin iniciar el servicio
docker-compose exec web bash -c "<comando>"  # Ejecutar bash en el contenedor
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
| `accounts/utils.py` | Función `send_email()` para envío de emails HTML con templates |
| `templates/email/base_email.html` | Template base para emails HTML (branding Andes Chile ONG) |
| `templates/email/generic.html` | Template genérico para emails (extiende base_email) |
| `apps/mediciones/models.py` | Device, TrafficCount |
| `apps/mediciones/views.py` | API IoT TrafficCountAPIView, DeviceRegisterView, DeviceNameUpdateView |
| `apps/mediciones/templates/mediciones/contador.html` | Aplicación de detección YOLO26n + ONNX (fingerprint, reverse geocoding, sync) |
| `hugo_edit/models.py` | Activity, Noticia, Estudio (genera .md y trigger rebuild Hugo via Celery) |
| `hugo_edit/tasks.py` | Tarea Celery `rebuild_hugo()` — ejecuta `hugo --minify` asincrónicamente |
| `hugo_edit/templatetags/split_tags.py` | Filtro personalizado `{% split "," %}` para separar tags en badges |
| `hugo_edit/management/commands/sync_hugo.py` | Comando sync DB → Hugo (actividades, noticias, estudios) |
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

### Control de Acceso (hugo_edit)

| Usuario | Email | is_active | is_staff | is_superuser |
|---|---|---|---|---|
| Francisco | francisco@andeschileong.cl | ✅ | ✅ | ✅ |
| Daniela | daniela@andeschileong.cl | ✅ | ✅ | ❌ |
| Juan | juan@andeschileong.cl | ✅ | ✅ | ❌ |
| Katherine | katherine@andeschileong.cl | ❌ | ❌ | ❌ |
| Natalia | natalia@andeschileong.cl | ✅ | ✅ | ❌ |
| Nicolas | nicolas@andeschileong.cl | ✅ | ✅ | ❌ |
| Pablo | pablo@andeschileong.cl | ✅ | ✅ | ❌ |
| Rafaela | rafaela@andeschileong.cl | ✅ | ✅ | ❌ |
| Rafael | rafael@andeschileong.cl | ✅ | ✅ | ❌ |
| Rodrigo | rodrigo@andeschileong.cl | ✅ | ✅ | ❌ |
| Sebastian | sebastian@andeschileong.cl | ✅ | ❌ | ❌ |

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
