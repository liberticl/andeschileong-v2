# PR: feat(contador): Sistema de conteo de tránsito YOLO26n + ONNX

**Base:** `master` ← **Head:** `feat/counter`

---

## Resumen

Sistema completo de detección y conteo de tránsito en tiempo real usando visión artificial en el navegador.

## Cambios principales

- Migración de TensorFlow.js a ONNX Runtime Web con modelo YOLO26n (9.5MB)
- Detección de 8 categorías: bicicletas, peatones, patinetes, autos, motos, buses, camiones, mascotas
- Backend adaptativo: WebGPU → WASM con fallback automático
- Selección de modelo por RAM: 320px (≤2GB) o 640px (>2GB)
- Auto-registro de dispositivos con fingerprint SHA-256
- Nombre legible por reverse geocoding (Nominatim)
- Sincronización periódica con localStorage para offline-resilience
- Token JWT con lookup por fingerprint (permite renombrar)
- Renombrar dispositivos desde la UI
- Re-registro automático si el token es inválido (401/403)
- Coordenadas a 5 decimales (~1m precisión)
- API docs en `docs/api.md`
- MongoDB polygon fix (dedup vértices)

## Archivos modificados

- `apps/mediciones/models.py` — +fingerprint field, token 512 chars
- `apps/mediciones/views.py` — DeviceRegisterView, DeviceNameUpdateView
- `apps/mediciones/auth.py` — Lookup por fingerprint en vez de name
- `apps/mediciones/urls.py` — +trafico/device/ endpoint
- `apps/mediciones/admin.py` — Campos nuevos en admin
- `apps/mediciones/templates/mediciones/contador.html` — UI completa
- `apps/mediciones/migrations/0005_`, `0006_` — Nuevas migraciones
- `ciudadespendientes/external_apis.py` — +reverse_geocode, +parse_device_name
- `andeschileong/settings.py` — CSRF_TRUSTED_ORIGINS con localhost
- `docs/api.md` — Documentación completa de endpoints
- `AGENTS.md`, `README.md` — Documentación actualizada

## Testing

1. Abrir `/apps/mediciones/contador/`
2. Verificar que el dispositivo se registra con nombre legible
3. Verificar que el conteo de tránsito funciona (ver colores en consola)
4. Renombrar desde el modal ⚙️
5. Verificar que el sync periódico funciona después de renombrar
