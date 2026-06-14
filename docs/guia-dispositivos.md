# Guía de Dispositivos — Sistema de Conteo de Tránsito

---

## 1. Resumen para No Técnicos

El **contador de tránsito** es una herramienta que usa la cámara de tu computador, celular o Raspberry Pi para contar automáticamente cuántas bicicletas, personas, patinetes, autos, motos, buses, camiones y mascotas pasan por un punto.

**Cómo funciona:**
1. Abres la página del contador en tu navegador
2. La cámara captura video en tiempo real
3. Una inteligencia artificial (YOLO26n) identifica los objetos en cada cuadro
4. Se dibuja una línea en pantalla — cuando algo cruza esa línea, se suma +1 al contador
5. Los datos se envían automáticamente al servidor cada 5 minutos

**Lo que necesitas:**
- Un dispositivo con cámara (computador, celular o Raspberry Pi)
- Un navegador moderno (Chrome, Firefox, Edge)
- Conexión a internet la primera vez (después funciona offline)

**No necesitas:**
- Instalar ningún programa
- Conocimientos técnicos
- Configurar servidores

---

## 2. Requisitos del Hardware

### Dispositivos compatibles

| Dispositivo | Rendimiento esperado | Notas |
|---|---|---|
| Computador de escritorio | 15-30 FPS | Cualquier CPU moderno |
| Laptop | 10-25 FPS | Depende del procesador |
| Celular gama media-alta | 8-15 FPS | Usar cámara trasera |
| Raspberry Pi 5 | ~7-8 FPS | Modelo 640px, WASM |
| Raspberry Pi 4 (2-4GB) | ~5-8 FPS | Modelo 320px o 640px |
| Raspberry Pi 3 (1GB) | ~2-3 FPS | Modelo 320px, mínimo viable |

### Cámara

- **Resolución ideal:** 1280×720 (720p)
- **Tipo:** Trasera preferida (mejor calidad óptica)
- **Ángulo:** Ver sección 5

### Memoria RAM

El sistema detecta automáticamente la RAM disponible y elige el modelo adecuado:

| RAM disponible | Modelo cargado | Entrada del modelo | Precisión |
|---|---|---|---|
| ≤ 2 GB | yolo26n-320 | 320×320 px | Menor, pero rápido |
| > 2 GB | yolo26n | 640×640 px | Mayor, más detallada |

---

## 3. Inicio Rápido

1. Abre tu navegador y ve a: **https://andeschileong.cl/apps/mediciones/contador/**
2. Acepta el uso de la cámara cuando el navegador lo pida
3. El sistema se auto-registra: espera ~3 segundos a que aparezca el badge verde "Conectado"
4. Haz clic en la línea roja punteada para posicionarla donde quieras contar
5. ¡Listo! Los conteos aparecen en tiempo real

### Cambiar el nombre del dispositivo

1. Haz clic en el ícono ⚙️ (configuración)
2. Escribe un nombre descriptivo (ej: "Av. Providencia esquina con Los Leones")
3. Guarda

### Cambiar la cámara

Haz clic en el ícono 🔄 para alternar entre cámara frontal y trasera.

---

## 4. Selección del Modelo

### ¿Qué modelo se usa?

El sistema usa **YOLO26n** (You Only Look Once, versión 26, variante nano), un modelo de detección de objetos optimizado para ser ligero y rápido.

### ¿Cómo se elige entre 320px y 640px?

```
RAM del dispositivo (navigator.deviceMemory)
         │
         ▼
    ≤ 2 GB ──→ Modelo 320px (ligero, ~9.8MB)
    > 2 GB ──→ Modelo 640px (preciso, ~9.5MB)
```

**Si el navegador no reporta RAM** (algunos navegadores no lo hacen), se asume 4 GB y se carga el modelo de 640px.

### Diferencias entre modelos

| Característica | 320px | 640px |
|---|---|---|
| Tamaño del archivo | 9.8 MB | 9.5 MB |
| Velocidad (Raspberry Pi 4) | ~8 FPS | ~5 FPS |
| Velocidad (computador) | ~30 FPS | ~20 FPS |
| Precisión en objetos pequeños | Menor | Mayor |
| Precisión en objetos grandes | Buena | Excelente |
| Uso de memoria | ~200 MB | ~400 MB |

**Recomendación:** Si tu dispositivo tiene más de 2 GB de RAM, usa el modelo 640px. Si es un Raspberry Pi o dispositivo con poca memoria, el 320px funciona bien.

### Backend de inferencia

El modelo puede ejecutarse con dos motores:

1. **WebGPU** (preferido): Usa la tarjeta gráfica del dispositivo. Más rápido.
2. **WASM** (fallback): Usa el procesador CPU. Funciona en todos los dispositivos.

El sistema intenta WebGPU primero. Si no está disponible, usa WASM automáticamente.

---

## 5. Posicionamiento de la Cámara

### Ángulo ideal

```
        CÁMARA (ángulo 30-45° desde arriba)
           \
            \  ← Línea de visión
             \
              \
    ════════════════════════  ← Línea de conteo (pavimento)
    ←        TRÁFICO       →
```

- **Ángulo recomendado:** 30° a 45° desde la vertical
- **¿Por qué?** Un ángulo inclinado permite que el modelo vea la forma completa de las personas y vehículos. Un ángulo muy bajo (casi horizontal) causa que los objetos se superpongan. Un ángulo muy alto (casi cenital) dificulta distinguir la dirección de movimiento.

### Altura de instalación

| Altura | Ventaja | Desventaja |
|---|---|---|
| 1.5 - 2 m | Fácil instalación, detalle facial | Puede haber obstrucciones |
| 2 - 3 m | Buena cobertura, menos obstrucciones | Requiere poste o estructura |
| 3 - 5 m | Cobertura amplia | Menos detalle, más parallax |

**Recomendación para conteo ciclista:** 2-3 metros de altura con ángulo de 30-40°.

### Dirección de la cámara

- **Cámara trasera (recomendada):** Se activa por defecto. Mejor calidad de imagen en la mayoría de dispositivos.
- **Cámara frontal:** Se usa si la trasera no está disponible. Útil para monitoreo desde un escritorio.

### Cobertura del frame

La cámara debe cubrir toda la sección de tráfico que quieres medir. Ajusta la posición para que:
- La línea de conteo cruce toda la calle
- Los vehículos y personas entren completamente en el frame antes de cruzar la línea
- No haya objetos estáticos (postes, árboles) directamente sobre la línea

---

## 6. Condiciones de Imagen

### Iluminación

| Condición | Impacto | Recomendación |
|---|---|---|
| Luz natural diurna | Óptimo | Sin cambios necesarios |
| Sombra parcial | Aceptable | Evitar sombras duras sobre la línea |
| Noche con alumbrado | Aceptable | Asegurar que la calle esté iluminada |
| Noche sin alumbrado | Malo | Instalar luz IR o LED blanca |
| Contraluz directo | Malo | Rotar cámara para evitar sol directo |

### Contraste y brillo

El sistema aplica automáticamente un filtro CSS que mejora la imagen:
- **Brillo:** +10% (`brightness(1.1)`)
- **Contraste:** +10% (`contrast(1.1)`)

Esto ayuda en condiciones de luz baja o imagen lavada.

### Factores que afectan la calidad

| Factor | Efecto | Solución |
|---|---|---|
| Gotas de lluvia en lente | Detecciones falsas | Cubrir con carcasa transparente |
| Reflexiones del sol | Blobs blancos, falsos positivos | Ángulo anti-reflejo o filtro polarizador |
| Niebla/bruma | Reduce contraste | Aumentar brillo del monitor, usar 640px |
| Movimiento borroso (motion blur) | Bounding boxes imprecisas | Aumentar iluminación |
| Resolución baja (<480p) | Objetos pequeños no detectados | Usar cámara de al menos 720p |

### Consejos para Raspberry Pi

- Usa una cámara con buen rendimiento en baja luz (sensor IMX477 o similar)
- Evita cámaras con resolución mayor a 1080p (innecesario y ralentiza)
- Monta la cámara en un lugar protegido de lluvia y polvo
- Considera un filtro IR-pass si vas a contar de noche

---

## 7. Línea de Conteó

### Cómo definir la línea

1. Haz clic en el botón **📏** (línea) en la parte superior
2. Se mostrará un overlay rojo sobre el video
3. Haz clic en el punto **A** (inicio de la línea)
4. Haz clic en el punto **B** (fin de la línea)
5. La línea se dibuja como una línea roja punteada

### Dirección de conteo

La línea tiene dos lados: **A** y **B**. El sistema cuenta en ambas direcciones:

```
    Lado A (abajo)
    ─────────────────  ← Línea de conteo
    Lado B (arriba)
```

- **A → B:** Cuenta como "subiendo" (por ejemplo: entrando a una ciclovia)
- **B → A:** Cuenta como "bajando" (por ejemplo: saliendo de una ciclovia)

### Deadzone (zona muerta)

La línea tiene una zona de 12 píxeles de tolerancia. Si un objeto está dentro de esa zona, se considera "sobre la línea" y no se cuenta como cruce hasta que salga completamente de ella.

Esto evita conteos duplicados cuando un objeto se mueve lentamente sobre la línea.

### Línea ideal

- **Orientación:** Preferiblemente perpendicular al flujo de tráfico
- **Longitud:** Que cubra todo el ancho de la calzada o ciclovía
- **Posición:** En un punto recto de la calle, no en una curva
- **Evitar:** Esquinas, semáforos, zonas de estacionamiento

### Sin línea (modo apariencia)

Si no dibujas línea, el sistema usa un modo alternativo:
- Cuenta cada objeto nuevo que aparece en el frame
- Solo cuenta una vez por objeto (requiere 3 cuadros estables)
- No distingue dirección
- Útil para conteo total en interiores o puntos sin flujo bidireccional

---

## 8. Categorías Detectables

El modelo detecta **8 categorías** basadas en las clases COCO:

| Categoría | Icono | Color | Clase COCO | Ejemplo |
|---|---|---|---|---|
| Bicicleta | 🚲 | Azul `#0066ff` | bicycle (1) | Bicicleta manual, e-bike |
| Peatón | 🚶 | Verde `#00ff00` | person (0) | Persona caminando |
| Patineta | 🛹 | Naranja `#ff6600` | skateboard (38) | Skate, patinetas, scooter |
| Auto | 🚗 | Rojo `#ef4444` | car (2) | Auto particular, SUV, van |
| Moto | 🏍️ | Naranja claro `#f97316` | motorcycle (3) | Motocicleta, scooter motorizado |
| Bus | 🚌 | Púrpura `#8b5cf6` | bus (5) | Bus urbano, micro |
| Camión | 🚚 | Rojo oscuro `#dc2626` | truck (7) | Camión de carga, furgón |
| Mascota | 🐕 | Verde esmeralda `#10b981` | dog (15), cat (16) | Perro o gato (comparten contador) |

### Notas importantes

- **Mascota:** Perros y gatos se cuentan juntos en el mismo contador
- **Patín:** Se detecta como "skateboard" — incluye patines, scooters manuales y monopatines eléctricos
- **Motos vs Bicicletas:** El modelo distingue entre ambos. Las motos suelen ser más anchas y tienen motor visible
- **Buses vs Camiones:** Diferenciados por tamaño y forma. Los buses son más largos yrectangulares

---

## 9. Lógica de Conteo

### Flujo de detección

```
Cámara → Cuadro → Modelo YOLO26n → Detecciones (bbox + clase + score)
                                          │
                                          ▼
                              Filtrar score < 0.50
                              Filtrar clases no rastreadas
                                          │
                                          ▼
                              Matching con tracks existentes
                              (IoU + distancia de centro)
                                          │
                                          ▼
                              Actualizar tracking (lado, movimiento)
                                          │
                                          ▼
                              ¿Cruzó la línea? → +1 al contador
```

### Parámetros de tracking

| Parámetro | Valor | Descripción |
|---|---|---|
| Confianza mínima | 50% | Detecciones por debajo de este valor se descartan |
| Vida máxima del track | 1500 ms | Si un objeto no se ve por 1.5 segundos, se elimina |
| Cuadros estables mínimos | 3 | Cuadros consecutivos que un objeto debe estar presente para contar (modo apariencia) |
| Enfriamiento entre conteos | 1200 ms | Tiempo mínimo entre dos conteos del mismo objeto |
| Deadzone de línea | 12 px | Zona alrededor de la línea donde el objeto se considera "en la línea" |
| Movimiento mínimo | 8 px | Un objeto debe moverse al menos 8 píxeles para que se registre un cruce |

### Matching de objetos (Asociación detección-track)

El sistema usa un algoritmo que combina:
1. **Distancia entre centros:** Qué tan cerca está el centro de la nueva detección del track existente
2. **IoU (Intersección sobre Unión):** Cuánto se superponen las cajas delimitadoras
3. **Tamaño adaptativo:** El radio de aceptación se adapta al tamaño del objeto (entre 60 y 180 píxeles)

```
Radio = max(60, min(180, diagonal_del_bbox × 0.8))
```

Esto significa que un auto grande tiene más tolerancia de movimiento que un peatón pequeño.

### Detección de cruce de línea

Un conteo se registra cuando:
1. El objeto estaba en un lado conocido de la línea
2. El objeto cruzó al otro lado (cambió de lado)
3. El objeto no estaba en la deadzone
4. Han pasado más de 1200 ms desde el último conteo de ese objeto
5. El objeto se ha movido al menos 8 píxeles en total

---

## 10. Sincronización de Datos

### Cómo funciona

Los conteos se acumulan localmente en el navegador y se envían al servidor periódicamente.

```
Conteo en tiempo real → Almacén local → POST /api/trafico/ → Servidor Django → PostgreSQL
```

### Intervalo de sincronización

- **Por defecto:** Cada 5 minutos
- **Configurable:** Desde 1 minuto hasta 1440 minutos (24 horas)
- **Cambiar:** Haz clic en ⚙️ → "Intervalo de sincronización (min)"

### Modo offline

Si pierdes la conexión a internet:
1. Los conteos se guardan en `localStorage` del navegador
2. Cuando recuperas conexión, se envían automáticamente
3. No se pierden datos

### Badges de estado

| Badge | Color | Significado |
|---|---|---|
| 🔴 Desconectado | Rojo | No hay token de dispositivo registrado |
| 🟡 Pendiente | Amarillo | Hay conteos sin enviar (offline o esperando sync) |
| 🟢 Conectado | Verde | Todo sincronizado, funcionando correctamente |

### Re-registro automático

Si el servidor rechaza el token (errores 401 o 403):
1. El sistema borra la configuración guardada
2. Se re-registra automáticamente con el mismo fingerprint
3. Obtiene un nuevo token
4. Continúa funcionando sin intervención del usuario

---

## 11. Registro y Nombre del Dispositivo

### Fingerprint (huella digital)

Cada dispositivo genera una "huella digital" única basada en:

| Componente | Ejemplo | Precisión |
|---|---|---|
| User-Agent del navegador | Mozilla/5.0 (Linux; Android 10) | Identifica navegador y SO |
| Resolución de pantalla | 1920x1080 | Identifica el dispositivo |
| Idioma | es-CL | Configuración regional |
| Zona horaria | America/Santiago | Ubicación geográfica |
| Núcleos de CPU | 8 | Capacidad del hardware |
| Coordenadas GPS | -33.4489,-70.6693 | Ubicación física (5 decimales, ~1m) |

Los 6 componentes se unen con `|||` y se hashean con **SHA-256**. El resultado es un string de 64 caracteres que identifica único al dispositivo+ubicación.

### Nombre del dispositivo

El nombre es una etiqueta legible generada automáticamente:

1. **Con GPS:** Se usa reverse geocoding (Nominatim) → "Providencia, Región Metropolitana"
2. **Sin GPS:** Se parsea el User-Agent → "Chrome 120 / Linux"
3. **Manual:** El usuario puede renombrar desde la interfaz (⚙️ → Nombre del dispositivo)

### Cambiar el nombre

1. Haz clic en ⚙️
2. Escribe el nuevo nombre (máximo 200 caracteres)
3. Haz clic en "Guardar nombre"
4. Se envía un PATCH al servidor: `PATCH /api/trafico/device/`

El nombre puede ser cualquier texto descriptivo:
- "Av. Italia esquina con Santa Isabel"
- "Ciclovía Providencia, lado norte"
- "Entrada parking_edificio_A"

---

## 12. Parámetros Técnicos Completos

### Modelo

| Parámetro | Valor |
|---|---|
| Modelo | YOLO26n (ultralytics) |
| Framework | ONNX Runtime Web 1.22.0 |
| Tamaño del modelo (640px) | 9.5 MB |
| Tamaño del modelo (320px) | 9.8 MB |
| Formato de salida | `[1, 300, 6]` (NMS-free) |
| Valores por detección | x1, y1, x2, y2, score, class_id |
| Normalización | pixel / 255.0 (rango [0, 1]) |
| Canales | RGB (CHW order) |
| Máximo de detecciones por cuadro | 300 |

### Cámara

| Parámetro | Valor |
|---|---|
| Resolución ideal | 1280×720 (720p) |
| Cámara por defecto | Trasera (environment) |
| Fallback | Frontal (user) si trasera falla |
| Audio | No capturado |
| CSS filter | `contrast(1.1) brightness(1.1)` |
| Object-fit | cover (recorta para llenar) |

### Tracking

| Parámetro | Valor |
|---|---|
| Algoritmo de matching | IoU + distancia de centro |
| Radio de aceptación | `max(60, min(180, diagonal × 0.8))` px |
| Umbral IoU para rechazo | < 0.05 |
| Bonus IoU en scoring | × 80 puntos |
| Vida del track | 1500 ms |
| Cuadros estables (modo apariencia) | 3 |
| Cooldown entre conteos | 1200 ms |
| Deadzone de línea | 12 px |
| Movimiento mínimo para cruce | 8 px |

### Sincronización

| Parámetro | Valor |
|---|---|
| Endpoint | `POST /api/trafico/` |
| Intervalo por defecto | 5 minutos |
| Intervalo configurable | 1 - 1440 minutos |
| Almacenamiento offline | localStorage |
| Re-registro automático | En errores 401/403 |
| Auth | Bearer token (JWT) |

### Fingerprint

| Parámetro | Valor |
|---|---|
| Algoritmo | SHA-256 |
| Componentes | 6 (UA, pantalla, idioma, timezone, cores, GPS) |
| Precisión GPS | 5 decimales (~1.1 metros) |
| Timeout GPS | 5000 ms |
| Delimitador | `\|\|\|` |

### Grabación y exportación

| Parámetro | Valor |
|---|---|
| FPS de grabación | 25 fps |
| Formato de video | WebM (VP9 o VP8) |
| Intervalo de chunks | 1000 ms |
| Formato de foto | PNG |
| Formato de CSV | UTF-8 con BOM |
| Nombre del CSV | `detecciones_eventos_YYYY-MM-DD.csv` |
| Nombre de foto | `foto_konta2r_<timestamp>.png` |
| Nombre de video | `grabacion_konta2r_<timestamp>.webm` |

---

## 13. Solución de Problemas

### El navegador no pide permiso de cámara

- Asegúrate de estar usando **HTTPS** (el navegador bloquea cámaras en HTTP)
- Verifica que no tengas la cámara bloqueada en la configuración del navegador
- Prueba en otro navegador (Chrome es el más compatible)

### El badge queda en rojo "Desconectado"

- Verifica tu conexión a internet
- Recarga la página (Ctrl+R o Cmd+R)
- Si persiste, el token puede estar vencido: borra los datos del sitio y recarga

### No detecta objetos

- Verifica que haya suficiente luz
- Asegúrate de que los objetos sean claramente visibles
- Intenta bajar el umbral de confianza si es posible (ajustar `CONFIDENCE_THRESHOLD` en el código)
- Asegúrate de que la cámara esté enfocada

### Cuenta de más o de menos

- Ajusta la línea para que sea perpendicular al flujo
- Asegúrate de que la línea cubra todo el ancho de la calle
- Verifica que no haya objetos estáticos (postes) sobre la línea
- El deadzone de 12px ayuda a evitar conteos duplicados

### El video se ve lento (pocos FPS)

- En Raspberry Pi, usa el modelo 320px
- Cierra otras pestañas del navegador
- Verifica que el backend sea WASM (no WebGPU si la GPU es débil)
- Reduce la resolución de la cámara

### Se pierden datos al cerrar el navegador

- Los conteos sin enviar se guardan en localStorage
- Al volver a abrir la página, se sincronizan automáticamente
- No cierres el navegador manualmente si hay badge amarillo "Pendiente"

### El nombre del dispositivo es incorrecto

- Haz clic en ⚙️ y renombrar manualmente
- El reverse geocoding depende de Nominatim (puede fallar si no hay GPS)
- Puedes poner cualquier nombre descriptivo

---

## 14. APIs Disponibles

Para integración con sistemas externos:

| Endpoint | Método | Auth | Descripción |
|---|---|---|---|
| `/api/trafico/register/` | POST | No | Auto-registrar dispositivo |
| `/api/trafico/` | POST | JWT | Enviar conteos de tránsito |
| `/api/trafico/device/` | PATCH | JWT | Renombrar dispositivo |
| `/apps/mediciones/contador/model/` | GET | No | Descargar modelo ONNX |

Documentación completa en: `docs/api.md`
