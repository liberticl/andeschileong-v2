# AndesChileOng / Ciudades Pendientes V2

Este es el proyecto "Ciudades Pendientes V2" para la ONG Andes Chile. Consta de una aplicación web construida en Django que permite la visualización inmersiva de datos de movilidad (uso de Strava, flujos ciclistas) mediante mapas interactivos utilizando librerías como DeckGL y Pydeck, combinadas con una arquitectura de persistencia de datos híbrida (PostgreSQL y MongoDB).

## 🧰 Tecnologías Principales

- **Backend:** Django 4.2, Django REST Framework.
- **Generador de Sitios Estáticos:** Hugo (versión Extendida).
- **Bases de Datos:** PostgreSQL (para modelos relacionales y usuarios) y MongoDB (para almacenamiento de trazas espaciales extensas).
- **Procesamiento Espacial y Visualización:** Pandas, GeoPandas, Pydeck, Deck.GL.
- **Despliegue y Contenerización:** Docker, Docker Compose, Nginx, Gunicorn.

---

## 🚀 Cómo ejecutar el proyecto

Para ejecutar el proyecto es imprescindible configurar un archivo `.env` en el directorio raíz. Dicho archivo deberá contener las variables definidas en `andeschileong/settings.py` (ej. `DB_HOST`, `MONGO_DB`, `SECRET_KEY`, credenciales PostgreSQL, etc.).

### Opción 1: Ejecución con Docker y Docker Compose (Recomendada)

El repositorio incluye un `Dockerfile` y un archivo `docker-compose.yml` listos para orquestar la aplicación (Django + Nginx). La imagen de Docker también se encarga de instalar automáticamente Hugo, compilar el sitio estático y sincronizarlo antes de arrancar los servicios.

1. Asegúrate de tener **Docker** y **Docker-Compose** instalados en tu sistema local.
2. Contar con el archivo `.env` correctamente configurado en la raíz de la carpeta.
3. Construir y levantar los contenedores:
   ```bash
   docker-compose up --build -d
   ```
   El entorno empaquetará la versión Slim de Python 3.11, instalará componentes al levantar `Gunicorn` sobre el puerto interno 8000, y lo expondrá vía `Nginx` en el puerto `80` localhost a la máquina anfitriona.
4. El proyecto estará disponible en: [http://localhost](http://localhost)
5. Para ejecutar migraciones o comandos administrativos en Django, ejecuta:
   ```bash
   docker-compose exec django python manage.py migrate
   docker-compose exec django python manage.py createsuperuser
   ```

### Opción 2: Ejecución Local de Desarrollo

1. Asegurarse de tener Python 3.11+ instalado.
2. Instalar **Hugo Extended** (versión recomendada: `0.121.2` o superior) en tu sistema local para la generación del contenido estático.
3. Clonar el repositorio y acceder a la raíz del proyecto.
4. Crear y activar un entorno virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
5. Instalar todas las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
6. Compilar el sitio de Hugo:
   ```bash
   cd hugo_site
   hugo --minify
   cd ..
   ```
7. Aplicar migraciones base, recolectar estáticos y sincronizar Hugo:
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   python manage.py sync_hugo
   ```
8. Levantar el servidor:
   ```bash
   python manage.py runserver
   ```
   El proyecto estará inicialmente disponible en [http://localhost:8000](http://localhost:8000).

---

## 🛠 Explicación del Código: Funciones Críticas

El proyecto organiza sus roles en torno distintas "apps" de Django. A continuación, se detallan las operaciones críticas en el código fuente.

### 1. Sistema de Mapeo Interactivo Strava (`ciudadespendientes/views.py`)

Las funcionalidades de renderizado territorial y de rutas de trayecto en Strava constituyen el corazón de la app `ciudadespendientes`:

- **`show_data(request)`**:
  Esta vista es la encargada de dibujar los mapas con sus respectivos polígonos. A nivel lógico, hace uso de decoradores exigentes: `@user_has_zone_permission` y `@user_has_permission(['view_strava_data'])` para constatar seguridad en el acceso. Luego recaba las entidades de `StravaData` mediante consultas a base relacional y desencadena el renderizado en conjunto del modelo espacial de MongoDB para retornarlo todo integrado inyectando los componentes al HTML de respuesta (`deckgl`).

- **`color_ride_map(city_bounds, center, years, collection, factor=1, anual=False)`**:
  Función pilar de la visualización web (WebGL).
  1. Utiliza `get_ride_from_mongo(...)` para hacer agregación geoespacial directa desde MongoDB y recuperar densidades de uso dentro del polígono respectivo de la ciudad.
  2. Implementa un proceso de categorización semántica sobre los trips, en rangos de "Bajo (Verde), Medio (Naranja), o Alto (Rojo)" usando `classify(...)` del modelo clasificador.
  3. Crea nativamente las instancias de clases `PyDeck/DeckGL` agrupando en la ruta el ID correspondiente para pintar la interfaz. Genera la visualización subyacente interactiva final.

### 2. Recolección de Datos desde Dispositivos IoT (`measuring/views.py`)

Existe una subaplicación dedicada a consumir lecturas de volumen de flujos enviadas por hardware.

- **`TrafficCountAPIView`**:
  Se trata de un Endpoint de la clase de `APIView` de Django REST. Permite recibir tráfico asincrónico utilizando `JSON`.
  - Revisa la existencia de JWT personalizados a nivel dispositivo, a fin de autenticar aparatos (`JWTAuthentication`).
  - Válida si el dispositivo en base de datos PostgreSQL se encuentra inhabilitado (`is_active = False`).
  - Procede a despachar los datos insertados mediante el módulo `TrafficCountSerializer`, actualizando la metadata general de medición de la ciudad permanentemente.

### 3. Conexiones Híbridas a Bases de Datos (`andeschileong/settings.py`)

El archivo de configuración asocia con gran protagonismo una arquitectura de dos DB paralelos:
- Utiliza la configuración tradicional de diccionarios `DATABASES` bajo motor `django.db.backends.postgresql` para manejar modelos de comportamiento, usuarios, áreas y relaciones rígidas.
- A nivel del bloque **# MongoDB info**, define mediante `MongoClient()` proveniente de `pymongo` el enlazado independiente con la base documental. Establece la instancia `STRAVA_COLLECTION`, un sistema de almacenamiento clave utilizado para realizar análisis y extracciones ultra masivas de polílagos espaciales que sobrepasarían las capacidades operáticas convencionales de PostGIS.

### 4. Integración del Generador Estático (Hugo) (`hugo_edit` y `hugo_site`)

El proyecto incluye un manejador de contenido estático apoyado en Hugo, ofreciendo alta velocidad en la entrega del sitio web de la fundación.
- **`hugo_site/`**: Contiene el proyecto de Hugo en sí (las plantillas, los layouts y el contenido en Markdown). Al ejecutar el comando `hugo` aquí dentro, se generan los archivos estáticos listos para ser servidos.
- **`hugo_edit/`**: Aplicación de Django diseñada para integrar la compilación y ofrecer un puente lógico. El comando de administración (`python manage.py sync_hugo`) asegura que el sitio de Hugo recién compilado se estructure y empaquete adecuadamente para ser despachado por Django y Nginx.