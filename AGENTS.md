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
| `accounts` | Sistema de autenticación custom: Account (custom user), Organization, Permission, RegistrationRequest, AccountActivationToken | `accounts/` |
| `measuring` | API IoT para dispositivos de conteo de tráfico: Device, TrafficCount | `measuring/` |
| `hugo_edit` | CMS para el sitio Hugo: CRUD de Actividades/Noticias/Estudios → genera .md → rebuild Hugo via Celery. Gestión de borradores, soft delete, papelera | `hugo_edit/` |
| `licitaciones` | Dashboard de licitaciones de infraestructura ciclista desde Mercado Público | `licitaciones/` |
| `emails` | Sistema de envío de correos masivos: Celery batch processing, logging, rotación de cuentas Gmail. Envío a usuarios, grupos, o listas externas | `emails/` |

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
| Estudios | `content/estudios/` | 2026/bahia-blanca (index.html + 3 mapas MapLibre/deck.gl con FullscreenControl + fix resize en fullscreen; los 3 recrean el `map` de MapLibre entero al estabilizar el resize/fullscreen (`recreateMap()` + `initOverlay()` + `hardRefreshDeck()`: el weightmap del HeatmapLayer de mapa1 quedaba congelado y sobrevivía a recrear overlay/capas)) y 2026/cicloamigable (HTML manual + `mapa-cerros.html` embebido (trackeado con `git add -f`, excepción al gitignore de estudios): réplica del mapa de Ciudades Pendientes para la comuna (polígono + regla + colores + tooltip + controles de la app, sin verdes) con años 2019/2024/2025 y botones zoom/rotar/ángulo/norte/fullscreen/captura PNG compuesta (tiles raster CARTO con CORS + flujos 2D del propio json, sin WebGL para no "tainted canvas"), generado por `oc_files/build_mapa_cp_valpo.py` dentro del contenedor; `map.html` con toolbar propia embebida en el archivo (zoom/rotar/ángulo/norte/fullscreen/captura por re-render oculto, no regenerar con `gen_map_real.py` que usa otro entorno); gráficos Chart.js con ver-grande (modal HD) + capturas PNG sin fondo / JPG fondo blanco en 3x con la proporción del sitio (render separado con datos clonados + opciones limpias sin símbolos + fuentes y anchos ×3 explícitos, `responsive:false`, canvas aparte — no tocar el gráfico vivo; ni `devicePixelRatio` ni `resize()` re-escalan en esta versión de Chart.js porque el resize se difiere si hay animación y el alto queda congelado); 2020/2023 vacíos y 2026/lo-vasquez (peregrinación ciclista Lo Vásquez 7–8 dic 2025 con Strava Metro: `index.html` narrativo con gráficos canvas nativos integrados —NO iframe: series, screenlines, comunas %/abs, dirección, puntos, Av. España, tablas y ficha de cálculo; datos JSON inline + JS `line/stackedBar/area2` con hover sincronizado/tooltip/pantalla completa por tarjeta, generados con `oc_files/gen_estudio_graficos.py` desde `oc_files/dashboard_lo_vasquez.html` + 2 mapas pydeck embebidos por iframe relativo; mapa 1 con panel mínimo (solo selección de capas en menú desplegable abajo-izquierda, contenido analítico en el index) y mapa 2 SIN capa verde (eliminada de raíz del JSON); ambos con barra `oc_files/map_toolbar.py` (zoom +/-, rotar ±15°, ángulo 0°/45°, norte, pantalla completa, captura PNG) que actúa vía `deckInstance.setProps({initialViewState})` + `onAfterRender`→`toBlob` (verificado contra deck.gl 9.3); Mapa 1 minimal vía `MAPA_MINIMAL=1 MAPA_OUT=...` en `gen_mapa_pydeck_v3.py`; test headless `oc_files/test_map_toolbar.py` con playwright+Chrome (vista/zoom/captura/sin errores JS); parcheo reproducible del estudio en `oc_files/patch_estudio_mapas.py`; regenerar mapas oc_files con `gen_mapa_pydeck_v3.py`/`gen_mapa_baron_reloj.py`, luego `cp` a content y public (public/ es root: borrar/copiar vía `docker compose exec`); `dashboard_lo_vasquez.html` NO existe en el estudio (contenido integrado); cada bloque de gráfico lleva su propio `<h3 class="chart-title">` (ahí se inyecta el botón ⛶; el JS del tablero busca `h3, h2` para servir a ambos documentos) con fallback a clase CSS `fs-full` si el navegador niega el fullscreen; leyendas fig6/fig7 = refugio/reloj según data-g6/g7 (el bug estaba en el template del tablero, se corrigió en origen en `gen_dashboard.py`); motor de dibujo con resize idempotente + `clearRect` en cada `draw()` en `ctx2d` (sin el clear, las guías del hover se acumulaban y ensuciaban el gráfico; verificado en Node con stubs; hover posterior SIN redibujar el canvas (a pedido UX 2026-11-16): la guía vertical, los puntos sobre las series y el recuadro de la barra se pintan en una CAPA DOM (`div.chart-overlay` dentro de `.chart-wrap`, estilos inline, `mkOverlay()`/`mkDot()` en `gen_dashboard.py`), no en el canvas — se sigue viendo la guía sin acumulación de guías fantasma ni zoom; la línea guía sigue al mouse y se sincroniza en los 3 gráficos de puntos (fig5/6/7); fig4 (áreas) recibió guía + tooltip; test headless `oc_files/test_guia_hover.py` (guía visible, sincronizada, canvas con bitmap idéntico antes/durante el hover, sin errores JS); las tablas de datos van FUERA de las tarjetas `section.card` (hermanas, no hijas); `gen_estudio_graficos.py` es idempotente (bloques `<!--G:...-->` + TITLES como única fuente del título del gráfico) (verificado); jerarquía de títulos unificada del sitio: h1 página → h2 de sección (`<h2 class="section-title">`, con línea inferior) → h3 del gráfico (`.gbloque h3.chart-title`, 1.1rem/700) → h4 para sub-títulos (Ventana A/B); en este estudio TODOS los títulos comparten el color del h2 (#333,Override local de `.content-section h3` que en el resto del sitio es azul #2241a8); el azul queda solo para acentos interactivos (summary, highlight-box, botón ⛶); los títulos de Mapa 1 / Mapa 2 / "Gráficos" también son `section-title` (antes usaban `.map-section h2` con otro tamaño) y se eliminó el h2 duplicado "Cómo leer estos gráficos" (TITLES["FIG:CALC"] = None); test headless `oc_files/test_titulos_estudio.py` (playwright+Chrome): jerarquía sin saltos, estilo de h3 igual al del sitio, botón ⛶ dentro del h3, sin `section.card` y sin errores de consola; los tres 'puntos fijos' (santuario/refugio/reloj) se publican como CICLISTAS/HORA ESTIMADAS: el cordón suma 6 segmentos troncales y se divide por 6 (quien cruza el cordón pisa los 6), conversión CALIBRADA contra el screenline del santuario (T2, un solo segmento) con desvío mediano 1,00 en 20 h (695/6 = 116 vs 115 medidos) y margen ±2,5 por el redondeo a 5 de Strava; el Reloj de Flores no tiene screenline de control, así que su cifra sirve para leer el desfase (peak 08h, una hora después del peak de Valparaíso 07h: la ola llega a Viña desde Valparaíso por Av. España, no desde Placilla); la conversión vive en el ORIGEN (`gen_dashboard.py`, `DIV_CORDON`/`_a_por_hora`) y `oc_files/patch_estudio_puntos_fijos.py` la propaga al index (NOTA: `gen_estudio_graficos.py` RE-SERIALIZA los bloques <!--G:...--> con el HTML compacto del tablero y borra el reformateo manual del index; por eso los cambios puntuales de contenido se aplican con ese parche quirúrgico, que es idempotente y verifica que el contenido final sea idéntico al del builder salvo espaciado); el gráfico de Av. España (fig8) publica UNA sola serie con el TOTAL de las dos calzadas del punto central ('Total Avenida España (Norte → Viña + Sur → Valparaíso)', peak 8dic - 09hrs con 85/h = 45+40; el detalle por dirección queda en la tabla, que suma la columna 'Total') — cambio pedido UX 2026-11-18, propagado con `oc_files/patch_estudio_av_espana.py`; los títulos que el usuario renombra dentro de bloques generados se alinean en TITLES (p. ej. FIG:4 = 'Sentido de pedaleo entre Lo Vásquez y Valparaíso') para que el builder no los revierta; el texto narrativo del usuario NUNCA se toca (parches solo sobre el contenido generado); el usuario QUITÓ del index los bloques 'Comunas por ventana' (FIG:TABLAS) y 'Cómo leer estos gráficos' (FIG:CALC) al reescribir la narrativa, así que `gen_estudio_graficos.py` ya no los genera (ORDER = FIG:1, FIG:2, FIG:567, FIG:3, FIG:4, FIG:8 + SCRIPTS) y las leyendas que el usuario reescribe dentro de bloques generados se alinean en el ORIGEN (ej. fig8 = 'Viajes con Strava en Avenida España'); 'Conclusiones generales' reescritas 2026-11-18 con el orden que pidió el autor (son las preguntas de la introducción): (1) hacia dónde se desplaza la gente —Casablanca/santuario con permanencia extendida, Valparaíso con base activa toda la noche (los que suben desde el puerto + los que vienen de Santiago sin detenerse), Viña a menor escala y 'otros' ~30% de los viajes activos la mañana del 8, aclarando que la lectura por comuna no es una matriz origen-destino; (2) las horas que ordenan el fenómeno (arranque tarde del 7, T1 270/h 03h, santuario ≈116/h 04h, descenso 05–07h con T3a 170/h y T4 130/h, Valparaíso 07h con el máximo de la red 44.315, desplome pos-mediodía); (3) Avenida España se usa de verdad (85/h a las 09h = 45+40, paridad entre calzadas como validación, corredor Valparaíso–Viña del Mapa 2, por eso Viña se llena desde Valparaíso y no desde Placilla, Reloj 08h una hora después, cifra referencial por la vereda de la calzada norte); (4) el cierre en ambos sentidos + vuelta a Santiago (18h–04h sube volumen desde la costa, T1 gira al este desde las 10h, refugio INSUCO en el eje del retorno ≈120/h a las 07h); (5) método y límite (screenlines, cordones ÷6 calibrados, sin factor de expansión) | el estudio lo-vasquez se publica en su URL pero NO aparece en el listado /estudios/: se logra con `_build: {list: never, render: always, publishResources: true}` en su front matter (lo saca de cualquier colección .Pages y del sitemap, pero la página y sus mapas se siguen publicando: verificado 200 en la URL y en los dos mapas); para volver a mostrarlo en el listado se borra ese bloque `_build` del front matter; OJO al versionar: `.gitignore` ignora `/hugo_site/content/estudios/*/`, así que hay que usar `git add -f hugo_site/content/estudios/2026/lo-vasquez/` (como bahia-blanca) | Manual (HTML) + **hugo_edit** (Django) |
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
| `RegistrationRequest` | accounts | Solicitudes de registro (status, sección, org, zona, revisión) |
| `AccountActivationToken` | accounts | Tokens UUID para activar cuenta (24h, uso único) |
| `Device` | mediciones | Dispositivos IoT: fingerprint (SHA-256), nombre legible, token JWT, coordenadas (5 dec), user_agent, last_seen |
| `TrafficCount` | mediciones | Registros de conteo vehicular: car, person, bicycle, motorcycle, truck, bus, skater, pet_count (totales) + línea A/B normalizada 0-1 (`line_x1..line_y2`, null = sin línea) + nombres de referencia (`side_a_name`/`side_b_name`) + desglose direccional `*_a_to_b` / `*_b_to_a` (total == A→B + B→A; convención A/B en `docs/api.md` §3 y `docs/guia-dispositivos.md` §7) |
| `Activity` | hugo_edit | Actividades del sitio Hugo (is_published, is_deleted) |
| `Noticia` | hugo_edit | Noticias del sitio Hugo (is_published, is_deleted) |
| `Estudio` | hugo_edit | Estudios del sitio Hugo (is_published, is_deleted) |
| `Licitacion` | licitaciones | Licitaciones de infraestructura ciclista/peatonal de Mercado Público |
| `SyncLog` | licitaciones | Logs de sincronización con API de Mercado Público |
| `SenderAccount` | emails | Cuentas Gmail para envío (email, display_name, daily_limit, is_active) |
| `EmailLog` | emails | Logs de correos enviados: destinatario, asunto, message_body (HTML con |safe), batch_id, estado (pending/sent/failed), error, sent_by, sent_at |

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
                          │
RegistrationRequest ──FK──→ Account (reviewed_by)
                     ──FK──→ Zone (zone, optional)
AccountActivationToken ──OneToOne──→ Account (user)
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

# CARTO Basemaps (https://carto.com/basemaps/apikey)
CARTO_API_KEY="..."           # Clave pública de tiles (sin ella: watermark "API KEY REQUIRED")

# Email (Gmail SMTP)
EMAIL_HOST_USER="contacto@andeschileong.cl"
EMAIL_HOST_PASSWORD="..."

# Email Batch Config (smtp-relay: 10,000/día por cuenta)
EMAIL_BATCH_SIZE=100
EMAIL_BATCH_DELAY_SECONDS=1
EMAIL_DAILY_LIMIT_PER_ACCOUNT=10000

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
| `/accounts/registro/` | `RegistrationRequestCreateView` | accounts | Solicitud de registro (pública) |
| `/accounts/solicitud-exitosa/` | `RegistrationRequestSuccessView` | accounts | Éxito solicitud |
| `/accounts/activar/<token>/` | `ActivateAccountView` | accounts | Activar cuenta con token |
| `/accounts/activacion-completa/` | `ActivationCompleteView` | accounts | Activación completada |
| `/accounts/password-reset/` | `PasswordResetView` | accounts | Formulario de restablecimiento |
| `/accounts/password-reset/done/` | `PasswordResetDoneView` | accounts | Correo enviado |
| `/accounts/password-reset/<uidb64>/<token>/` | `PasswordResetConfirmView` | accounts | Nueva contraseña |
| `/accounts/password-reset-complete/` | `PasswordResetCompleteView` | accounts | Contraseña restablecida |
| `/accounts/api/zonas/` | `ZonesAPIView` | accounts | API JSON zonas (fetch) |
| `/accounts/api/regiones/` | `RegionsAPIView` | accounts | API JSON regiones por país |
| `/accounts/api/comunas/` | `ComunasByRegionAPIView` | accounts | API JSON comunas por región |
| `/accounts/api/organizaciones/` | `OrganizationsAPIView` | accounts | API JSON organizaciones activas |
| `/intranet/correos/` | `email_logs` | emails | Historial de envíos (staff, una fila por batch_id: agrupa solo por batch_id con Min(batch_label/sent_by/created_at)) |
| `/intranet/correos/nuevo/` | `compose_email` | emails | Formulario de envío de correos (staff) |
| `/intranet/correos/cuentas/` | `sender_accounts` | emails | Cuentas remitentes configuradas (staff) |
| `/intranet/correos/<batch_id>/` | `email_log_detail` | emails | Detalle de un lote de envío (staff, con previsualización iframe sandbox srcdoc del HTML final renderizado con `first_log.template_name or 'email/generic.html'` → `preview_html`; fallback a message_body si el template falta) |
| `/intranet/correos/<batch_id>/reintentar/` | `email_retry_failed` | emails | Reintentar envíos fallidos (staff) |
| `/intranet/solicitudes/` | `RegistrationRequestListView` | hugo_edit | Listado solicitudes (staff) |
| `/intranet/solicitudes/<pk>/` | `RegistrationRequestDetailView` | hugo_edit | Detalle solicitud (staff) |
| `/intranet/solicitudes/<pk>/aprobar/` | `RegistrationRequestApproveView` | hugo_edit | Aprobar solicitud (staff) |
| `/intranet/solicitudes/<pk>/rechazar/` | `RegistrationRequestRejectView` | hugo_edit | Rechazar solicitud (staff) |
| `/recursos/` | `welcome` | ciudadespendientes | Dashboard principal |
| `/recursos/ciudadespendientes/` | `find` | ciudadespendientes | Búsqueda de datos |
| `/recursos/ciudadespendientes/mapa/` | `show_data` | ciudadespendientes | Mapa interactivo DeckGL |
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
| `/recursos/mediciones/contador/` | `contador` | mediciones | Contador de tránsito (ONNX + YOLO26n) |
| `/recursos/mediciones/contador/model/` | `contador_model` | mediciones | Modelo ONNX (320/640px según RAM) |
| `/recursos/mediciones/contador-externo/` | `contador_externo` | mediciones | Contador fuente externa (tabs URL/archivo local, MP4/WEBM + HLS .m3u8 via hls.js + MJPEG, no acepta watch?v= YouTube directo: extraer .m3u8 con `yt-dlp -g`) |
| `/api/trafico/` | `TrafficCountAPIView` | mediciones | API IoT (JWT auth). POST totales (backward-compatible) + opcional `line: {x1,y1,x2,y2} \| null` y `direction_counts: {a_to_b, b_to_a}` (valida total == A→B + B→A o lo deriva; `line` requerida con dirección; `line: null` = aparición). Ver `docs/api.md` §3 |
| `/api/trafico/register/` | `DeviceRegisterView` | mediciones | Auto-registro de dispositivos (sin auth) |
| `/api/trafico/device/` | `DeviceNameUpdateView` | mediciones | Renombrar dispositivo (JWT auth) |
| `/recursos/licitaciones/` | `dashboard` | licitaciones | Dashboard licitaciones ciclistas |
| `/recursos/licitaciones/lista/` | `licitaciones_list` | licitaciones | Listado de licitaciones |
| `/recursos/licitaciones/<codigo>/` | `licitacion_detalle` | licitaciones | Detalle + adjudicación (monto/proveedor/acta/diferencia abreviada) + timeline horizontal 5 hitos dd/mm/yyyy, azul=solo fechas pasadas + badge cierre; botón MP responsive |
| `/recursos/licitaciones/api/stats/` | `api_stats` | licitaciones | API JSON para charts |

---

## 10. Docker

### Levantar

```bash
docker-compose up --build -d
```

### Hot reload (ver cambios en el navegador sin rebuild)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d web redis
# sitio en http://localhost (Hugo --watch reconstruye public/ al guardar;
# gunicorn --reload recarga Django; basta recargar el navegador)
```

El servicio `web` de `docker-compose.dev.yml` monta `.:/andeschileong/` y corre
`hugo --watch --poll 700ms` en segundo plano (polling porque inotify no cruza el
bind mount), por lo que editar `hugo_site/content/...` (ej. `estudios/2026/cicloamigable/index.html`) se refleja
con solo guardar + recargar. No rebuildear ni reiniciar.

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

# Backfill adjudicación desde raw_data (sin API): monto_adjudicado,
# proveedor, oferentes, acta, reclamos BETA
python manage.py rellenar_adjudicacion
python manage.py rellenar_adjudicacion --dry-run
python manage.py rellenar_adjudicacion --codigo 2483-189-LP26

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
| `andeschileong/settings.py` | Configuración principal (DBs, apps, Hugo, colores capas, CARTO_API_KEY) |
| `andeschileong/context_processors.py` | Expone `CARTO_API_KEY` a los templates (tiles Leaflet) |
| `andeschileong/urls.py` | URL routing principal |
| `ciudadespendientes/models.py` | Zone, StravaData, GeoRegionBoundary |
| `ciudadespendientes/views.py` | show_data, color_ride_map, welcome, find |
| `ciudadespendientes/utils.py` | Funciones geo, MongoDB, DeckGL HTML, `get_carto_map_style()` (devuelve **str** URL del estilo Positron con `?key=`; pydeck 0.9.x revienta si `map_style` es dict) |
| `ciudadespendientes/mongodb.py` | Pipelines de agregación MongoDB |
| `ciudadespendientes/classifier.py` | Clasificación de flujos (SECTRA, general) |
| `ciudadespendientes/choices.py` | Constantes: regiones, países, meses, años |
| `ciudadespendientes/admin.py` | Admin con upload ZIP a MongoDB |
| `ciudadespendientes/external_apis.py` | Geocodificación (local first → OSM fallback), reverse geocoding, parse User-Agent |
| `ciudadespendientes/management/commands/download_chile_boundaries.py` | Descarga polígonos comunas Chile |
| `accounts/models.py` | Account, Organization, Permission, RegistrationRequest, AccountActivationToken |
| `accounts/choices.py` | ORGANIZATION_TYPES, ACCESS_SECTIONS, REQUEST_STATUS |
| `accounts/forms.py` | AccountCreationForm, AccountChangeForm, RegistrationRequestForm, RegistrationRequestRejectForm |
| `accounts/views.py` | CustomLoginView, StaffMixin, RegistrationRequest views, ActivateAccountView, ZonesAPIView, RegionsAPIView, ComunasByRegionAPIView, OrganizationsAPIView |
| `accounts/urls.py` | URLs de registro, activación, solicitudes (staff), API zonas |
| `accounts/utils.py` | Función `send_email()` para envío de emails HTML con templates |
| `templates/email/base_email.html` | Template base para emails HTML (branding Andes Chile ONG) |
| `templates/email/generic.html` | Template genérico para emails (extiende base_email, renderiza message_body con \|safe) |
| `templates/email/welcome.html` | Email de bienvenida con link de activación |
| `templates/email/registration_rejected.html` | Email de rechazo de solicitud |
| `templates/email/new_registration_request.html` | Email de notificación al admin |
| `templates/email/password_reset.html` | Email de restablecimiento de contraseña |
| `templates/email/password_reset_subject.txt` | Asunto del email de reset |
| `templates/accounts/registration_request.html` | Formulario 2 pasos de solicitud (JS) |
| `templates/accounts/registration_request_list.html` | Listado de solicitudes (staff) |
| `templates/accounts/registration_request_detail.html` | Detalle solicitud + aprobar/rechazar |
| `templates/accounts/activate_account.html` | Formulario para establecer contraseña |
| `templates/accounts/activation_complete.html` | Página de éxito de activación |
| `templates/accounts/password_reset_request.html` | Formulario de solicitud de reset |
| `templates/accounts/password_reset_done.html` | Confirmación de envío de correo |
| `templates/accounts/password_reset_confirm.html` | Formulario de nueva contraseña |
| `templates/accounts/password_reset_complete.html` | Confirmación de reset completado |
| `recursos/mediciones/models.py` | Device, TrafficCount |
| `recursos/mediciones/views.py` | API IoT TrafficCountAPIView, DeviceRegisterView, DeviceNameUpdateView |
| `apps/mediciones/models.py` | Device, TrafficCount (totales + `line_x1..line_y2` nullables 0-1 + `*_a_to_b`/`*_b_to_a`; `has_line`, `has_direction_data`, `get_line_dict()`, `get_direction_counts_dict()`) |
| `apps/mediciones/serializers.py` | TrafficCountSerializer (acepta totales planos + `line`/`direction_counts`/`side_names` anidados o planos; valida total == A→B+B→A o deriva; responde totales + `line` + `direction_counts` + `side_names`) |
| `apps/mediciones/admin.py` | Admin Device + TrafficCount (listado con `direction_summary`/`line_summary`, fieldsets Totales/Línea A→B/Dirección A→B/B→A) |
| `apps/mediciones/migrations/0007_trafficcount_bicycle_a_to_b_and_more.py` | Línea + 16 campos direccionales |
| `apps/mediciones/migrations/0008_trafficcount_side_a_name_trafficcount_side_b_name.py` | Nombres de referencia `side_a_name`/`side_b_name` |
| `recursos/mediciones/templates/mediciones/contador.html` | Aplicación de detección YOLO26n + ONNX (fingerprint, reverse geocoding, sync). Línea A/B: `signedDistance` footPoint ±12px, `A->B` −1→+1; overlay con etiquetas de lado A/B + nombres de referencia configurables (⚙️, van en eventos/CSV/`side_names`); sync envía `line` + `direction_counts` + `side_names` (pending dir en `traffic_pending_dir`, se descarta si la línea cambió) |
| `apps/mediciones/templates/mediciones/contador_externo.html` | Contador externo: tabs URL/archivo local (archivo local via `URL.createObjectURL`, HLS `.m3u8` con hls.js CDN + fallback nativo Safari y `destroy()` en `stopCurrentSource()`, `<video crossorigin="anonymous">` + logs CORS, hint MP4/WEBM/HLS/MJPEG sin `watch?v=` — usar `yt-dlp -g`). Misma lógica A/B + etiquetas de lado + sync direccional que `contador.html` |
| `hugo_edit/models.py` | Activity, Noticia, Estudio (genera .md y trigger rebuild Hugo via Celery) |
| `hugo_edit/tasks.py` | Tarea Celery `rebuild_hugo()` — ejecuta `hugo --minify` asincrónicamente |
| `hugo_edit/templatetags/split_tags.py` | Filtro personalizado `{% split "," %}` para separar tags en badges |
| `hugo_edit/management/commands/sync_hugo.py` | Comando sync DB → Hugo (actividades, noticias, estudios) |
| `hugo_edit/admin.py` | Admin custom con SimpleMDE |
| `licitaciones/models.py` | Licitacion (monto_estimado + monto_adjudicado/proveedor_adjudicado/n_oferentes/url_acta/n_reclamos BETA; get_monto_principal = adjudicado si adjudicada), SyncLog |
| `licitaciones/views.py` | Dashboard (KPIs año efectivo: total/publicadas/adjudicadas/monto adjudicado + sub estimado), listado, detalle (timeline horizontal 5 hitos dd/mm/yyyy, azul=solo fechas pasadas, + badge cierre + diferencia abreviada), api_stats |
| `licitaciones/urls.py` | URLs de licitaciones |
| `licitaciones/admin.py` | Admin con filtros y acciones |
| `licitaciones/forms.py` | Formulario de filtros (FiltroLicitacionesForm con comuna, región, año, estado) |
| `licitaciones/management/commands/sync_licitaciones.py` | Sync con API Mercado Público |
| `licitaciones/management/commands/rellenar_adjudicacion.py` | Backfill adjudicación desde raw_data (offline) |
| `licitaciones/migrations/0002_adjudicacion.py` | Campos adjudicación + reclamos BETA |
| `licitaciones/templates/licitaciones/` | Templates del dashboard |
| `hugo_site/config.toml` | Configuración de Hugo |
| `hugo_site/layouts/` | Layouts y partials customizados |
| `hugo_site/content/` | Contenido Markdown del sitio |
| `hugo_site/assets/css/main.css` | CSS custom del sitio |
| `templates/` | Templates Django (base con mapa Leaflet + `?key={{ CARTO_API_KEY }}`, navbar, 404, 403) |
| `Dockerfile` | Configuración de Docker |
| `entrypoint.sh` | Arranque: si recibe comando (compose dev) lo ejecuta en vez del flujo prod — así corre `hugo --watch` + `gunicorn --reload`. Sin comando: sync_hugo → nginx → gunicorn |
| `docker-compose.yml` | Orquestación Docker |
| `requirements.txt` | Dependencias Python |
| `.env` | Variables de entorno |
| `docs/api.md` | Documentación de API para endpoints de tránsito (§3: totales + `line`/`direction_counts` A→B/B→A, curl con/sin dirección) |
| `docs/guia-dispositivos.md` | Guía completa para dispositivos de conteo (§7: convención A/B, signedDistance ±12px, etiquetas overlay, `line: null` = aparición) |

---

## 13. Convención de Botones

El botón estándar del sitio se define en `ciudadespendientes/static/ciudadespendientes/main.css` (línea 128):

| Propiedad | Valor |
|---|---|
| Clase | `class="btn"` |
| Fondo | `white` |
| Borde | `2px solid #2241a8` |
| Texto | `black` |
| Border-radius | `0.375rem` (Bootstrap 5 default) |
| Hover - fondo | `#2241a8` |
| Hover - texto | `white` |

**No usar** `ac-btn-primary` (fondo azul sólido). Usar siempre `class="btn"` para botones principales.

**Excepción intranet/correos:** `log_list.html` usa `btn-primary` (Nuevo envío) y `btn-outline-primary` (eye). El hover blanco se fuerza en `main.css` (bloque "Intranet button hover"): `.btn-primary:hover` y `.btn-outline-primary:hover` (+ hijos `.fa` y variantes `a.btn-...`) con `color:#fff !important` y `background/border-color:#2241a8 !important` para outline-primary. No tocar el estilo de Volver (`btn-outline-secondary`, ya bien).

---

## 14. Constantes de Configuración

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
