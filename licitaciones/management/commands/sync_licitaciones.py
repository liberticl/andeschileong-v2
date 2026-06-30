from django.core.management.base import BaseCommand
import requests
import os
import re
import time
from datetime import date, timedelta

from licitaciones.models import Licitacion, SyncLog

KEYWORDS_INFRAESTRUCTURA = [
    'ciclovía', 'ciclovia', 'cicloruta', 'ciclo ruta',
    'andén', 'anden', 'peatonal', 'peaton',
    'bicicleta', 'bici', 'ciclismo',
    'seguridad vial', 'mobiliario urbano',
    'infraestructura ciclista', 'vía verde', 'via verde',
    'carril bici', 'sendero ciclista',
]

ESTADO_MAP = {
    5: 'publicada',
    6: 'cerrada',
    7: 'desierta',
    8: 'adjudicada',
    18: 'revocada',
    19: 'suspendida',
}

API_BASE = 'https://api.mercadopublico.cl/servicios/v1/publico/'


class Command(BaseCommand):
    help = 'Sincroniza licitaciones de Mercado Público'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias', type=int, default=7,
            help='Días hacia atrás para buscar')
        parser.add_argument(
            '--ticket', type=str, default=None,
            help='Ticket de API (default: MERCADO_PUBLICO_TICKET env)')

    def handle(self, *args, **options):
        ticket = options['ticket'] or os.environ.get('MERCADO_PUBLICO_TICKET')
        if not ticket:
            self.stdout.write(self.style.ERROR(
                'No se encontró ticket. '
                'Usa --ticket o configura MERCADO_PUBLICO_TICKET en .env'))
            return

        dias = options['dias']
        start_time = time.time()
        consultadas = 0
        filtradas = 0
        nuevas = 0
        actualizadas = 0
        errores = 0
        detalles_ok = 0

        keywords_lower = [k.lower() for k in KEYWORDS_INFRAESTRUCTURA]

        for i in range(dias):
            fecha = date.today() - timedelta(days=i)
            fecha_str = fecha.strftime('%d%m%Y')
            url = f'{API_BASE}licitaciones.json'
            params = {'fecha': fecha_str, 'ticket': ticket}

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                licitaciones = data.get('Listado', [])
                consultadas += len(licitaciones)

                for lic in licitaciones:
                    nombre = lic.get('Nombre', '').lower()
                    if not any(k in nombre for k in keywords_lower):
                        continue

                    filtradas += 1
                    codigo = lic['CodigoExterno']

                    detail = self._fetch_detalle(codigo, ticket)
                    if detail:
                        detalles_ok += 1
                        merged = {**lic, **detail}
                    else:
                        merged = lic
                        errores += 1

                    mapped = self._map_licitacion(merged)
                    obj, created = (
                        Licitacion.objects
                        .update_or_create(
                            codigo=codigo,
                            defaults=mapped)
                    )
                    if created:
                        nuevas += 1
                    else:
                        actualizadas += 1

                    time.sleep(1.0)

            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(
                    f'Error en fecha {fecha_str}: {e}'))

        # Segunda pasada: re-fetch de licitaciones que quedaron sin organismo
        incompletas = Licitacion.objects.filter(
            activo=True, organismo='')
        if incompletas.exists():
            self.stdout.write(
                f'\nRe-fetching {incompletas.count()} '
                f'licitaciones sin organismo...')
            for lic in incompletas:
                try:
                    detail = self._fetch_detalle(lic.codigo, ticket)
                    if detail:
                        self._apply_detail(lic, detail)
                        lic.save()
                        self.stdout.write(
                            f'  OK: {lic.codigo} -> '
                            f'{lic.organismo[:40] or "(sin organismo)"}')
                    time.sleep(1.0)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'Error re-fetch {lic.codigo}: {e}'))

        duracion = time.time() - start_time
        SyncLog.objects.create(
            licitaciones_consultadas=consultadas,
            licitaciones_filtradas=filtradas,
            licitaciones_nuevas=nuevas,
            licitaciones_actualizadas=actualizadas,
            errores=errores,
            duracion_segundos=duracion,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Sync completada: {nuevas} nuevas, {actualizadas} actualizadas, '
            f'{filtradas} filtradas de {consultadas} consultadas, '
            f'{detalles_ok} detalles OK ({duracion:.1f}s)'))

    def _fetch_detalle(self, codigo, ticket, max_retries=3):
        """Obtiene el detalle completo de una licitación con reintentos."""
        url = f'{API_BASE}licitaciones.json'
        params = {'codigo': codigo, 'ticket': ticket}
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                listado = data.get('Listado', [])
                if listado:
                    return listado[0]
                if 'CodigoExterno' in data:
                    return data
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    time.sleep(wait)
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Error fetching detalle {codigo} '
                        f'({max_retries} intentos): {e}'))
                    return None

    def _apply_detail(self, lic, detail):
        """Aplica datos del detalle a un objeto Licitacion existente."""
        comprador = detail.get('Comprador', {})
        if comprador and isinstance(comprador, dict):
            lic.organismo = comprador.get('NombreOrganismo', '') or ''
            try:
                lic.codigo_organismo = int(
                    comprador.get('CodigoOrganismo', 0))
            except (ValueError, TypeError):
                lic.codigo_organismo = None
            lic.region = (
                comprador.get('RegionUnidad', '') or '').strip()
            lic.comuna = (
                comprador.get('ComunaUnidad', '') or '').strip()

        monto = detail.get('MontoEstimado')
        try:
            lic.monto_estimado = float(monto) if monto else None
        except (ValueError, TypeError):
            lic.monto_estimado = None

        fechas = detail.get('Fechas', {}) or {}
        if fechas.get('FechaPublicacion'):
            lic.fecha_publicacion = fechas['FechaPublicacion']
        if fechas.get('FechaCierre'):
            lic.fecha_cierre = fechas['FechaCierre']

        lic.raw_data = detail

    def _map_licitacion(self, lic):
        organismo = ''
        codigo_organismo = None
        region_unidad = ''
        comuna_unidad = ''
        comprador = lic.get('Comprador', {})
        if comprador and isinstance(comprador, dict):
            organismo = comprador.get('NombreOrganismo', '')
            try:
                codigo_organismo = int(comprador.get('CodigoOrganismo', 0))
            except (ValueError, TypeError):
                codigo_organismo = None
            region_unidad = (comprador.get('RegionUnidad', '') or '').strip()
            comuna_unidad = (comprador.get('ComunaUnidad', '') or '').strip()

        estado_code = lic.get('CodigoEstado', 0)
        try:
            estado_code = int(estado_code)
        except (ValueError, TypeError):
            estado_code = 0
        estado = ESTADO_MAP.get(estado_code, 'publicada')

        monto = lic.get('MontoEstimado')
        try:
            monto = float(monto) if monto else None
        except (ValueError, TypeError):
            monto = None

        tipo = lic.get('Tipo', '')
        if not tipo:
            tipo = self._detectar_tipo(lic.get('CodigoExterno', ''))

        fechas = lic.get('Fechas', {}) or {}
        fecha_pub = fechas.get('FechaPublicacion') or lic.get('FechaPublicacion')
        fecha_cierre = fechas.get('FechaCierre') or lic.get('FechaCierre')

        return {
            'nombre': lic.get('Nombre', ''),
            'organismo': organismo,
            'codigo_organismo': codigo_organismo,
            'monto_estimado': monto,
            'moneda': lic.get('Moneda', 'CLP'),
            'estado': estado,
            'fecha_cierre': fecha_cierre,
            'fecha_publicacion': fecha_pub,
            'tipo_licitacion': tipo[:5] if tipo else '',
            'comuna': comuna_unidad,
            'region': region_unidad,
            'palabras_clave': self._extract_keywords(
                lic.get('Nombre', '')),
            'raw_data': lic,
        }

    def _detectar_tipo(self, codigo):
        """Detecta tipo de licitación desde el código (ej: LE26, LP26, L126)."""
        if not codigo:
            return ''
        match = re.search(r'-(L[A-Z0-9]+)\d{2}$', codigo)
        if match:
            return match.group(1)
        return ''

    def _extract_keywords(self, nombre):
        nombre_lower = nombre.lower()
        return [
            kw for kw in KEYWORDS_INFRAESTRUCTURA
            if kw.lower() in nombre_lower
        ]
