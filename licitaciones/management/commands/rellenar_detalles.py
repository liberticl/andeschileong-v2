from django.core.management.base import BaseCommand
import requests
import os
import time

from licitaciones.models import Licitacion


API_BASE = 'https://api.mercadopublico.cl/servicios/v1/publico/'


class Command(BaseCommand):
    help = 'Re-obtiene el detalle de licitaciones que tienen organismo vacío'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ticket', type=str, default=None,
            help='Ticket de API (default: MERCADO_PUBLICO_TICKET env)')
        parser.add_argument(
            '--codigo', type=str, default=None,
            help='Re-fetch solo un código específico')

    def handle(self, *args, **options):
        ticket = options['ticket'] or os.environ.get('MERCADO_PUBLICO_TICKET')
        if not ticket:
            self.stdout.write(self.style.ERROR(
                'No se encontró ticket. '
                'Usa --ticket o configura MERCADO_PUBLICO_TICKET en .env'))
            return

        if options['codigo']:
            qs = Licitacion.objects.filter(
                codigo=options['codigo'], activo=True)
        else:
            qs = Licitacion.objects.filter(
                activo=True, organismo='')

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                'No hay licitaciones sin organismo para re-fetch.'))
            return

        self.stdout.write(
            f'Encontradas {total} licitaciones sin organismo. '
            f'Re-obteniendo detalle...')

        actualizadas = 0
        errores = 0

        for lic in qs:
            try:
                url = f'{API_BASE}licitaciones.json'
                params = {'codigo': lic.codigo, 'ticket': ticket}
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                listado = data.get('Listado', [])
                detail = listado[0] if listado else (
                    data if 'CodigoExterno' in data else None)

                if not detail:
                    self.stdout.write(self.style.WARNING(
                        f'Sin detalle para {lic.codigo}'))
                    errores += 1
                    continue

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
                lic.save()
                actualizadas += 1
                self.stdout.write(
                    f'  OK: {lic.codigo} -> '
                    f'{lic.organismo[:40] or "(sin organismo)"}')

                time.sleep(1.0)

            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(
                    f'Error en {lic.codigo}: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'Completado: {actualizadas} actualizadas, '
            f'{errores} errores de {total} procesadas'))
