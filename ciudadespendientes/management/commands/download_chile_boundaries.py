"""
Comando para descargar y almacenar límites geográficos de Chile.
Fuentes: caracena/chile-GeoJSON (datos del IGM/SUBDERE).
"""
import json
import requests
from django.core.management.base import BaseCommand
from ciudadespendientes.models import GeoRegionBoundary


# Repositorio con polígonos de comunas por región (1-16)
CHILE_GEOJSON_BASE_URL = (
    "https://raw.githubusercontent.com/caracena/chile-geojson/master"
)

# Códigos de región a nombre normalizado
REGION_CODE_MAP = {
    1: "Arica y Parinacota",
    2: "Tarapacá",
    3: "Antofagasta",
    4: "Atacama",
    5: "Coquimbo",
    6: "Valparaíso",
    7: "Región Metropolitana",
    8: "O Higgins",
    9: "Maule",
    10: "Ñuble",
    11: "Biobío",
    12: "La Araucanía",
    13: "Los Ríos",
    14: "Los Lagos",
    15: "Aysén",
    16: "Magallanes",
}

# Mapeo de nombres de regiones que pueden venir en los datos
REGION_NAME_MAP = {
    "Arica y Parinacota": "Arica y Parinacota",
    "Arica": "Arica y Parinacota",
    "Parinacota": "Arica y Parinacota",
    "Tarapacá": "Tarapacá",
    "Iquique": "Tarapacá",
    "Antofagasta": "Antofagasta",
    "Atacama": "Atacama",
    "Coquimbo": "Coquimbo",
    "Valparaíso": "Valparaíso",
    "Metropolitana de Santiago": "Región Metropolitana",
    "Región Metropolitana de Santiago": "Región Metropolitana",
    "Santiago": "Región Metropolitana",
    "O'Higgins": "O Higgins",
    "O Higgins": "O Higgins",
    "Colchagua": "O Higgins",
    "Cardenal Caro": "O Higgins",
    "Maule": "Maule",
    "Ñuble": "Ñuble",
    "Biobío": "Biobío",
    "La Araucanía": "La Araucanía",
    "Los Ríos": "Los Ríos",
    "Los Lagos": "Los Lagos",
    "Aysén": "Aysén",
    "Magallanes": "Magallanes",
    "Magallanes y la Antártica Chilena": "Magallanes",
}


class Command(BaseCommand):
    help = 'Descarga y almacena límites geográficos de comunas de Chile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='github',
            help='Fuente de datos: github (default), catastro'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar datos existentes antes de descargar'
        )

    def handle(self, *args, **options):
        source = options['source']
        clear = options['clear']

        if clear:
            self.stdout.write('Limpiando límites geográficos existentes...')
            GeoRegionBoundary.objects.filter(country='Chile').delete()

        self.stdout.write(f'Descargando límites geográficos de Chile desde {source}...')

        if source == 'github':
            self.download_from_github()
        else:
            self.stdout.write(self.style.ERROR(f'Fuente no soportada: {source}'))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Proceso completado. Total: {GeoRegionBoundary.objects.filter(country="Chile").count()} límites.'
        ))

    def download_from_github(self):
        """Descarga polígonos desde el repositorio GitHub de caracena/chile-geojson."""
        total_created = 0
        total_updated = 0
        total_errors = 0

        for region_code, region_name in REGION_CODE_MAP.items():
            url = f"{CHILE_GEOJSON_BASE_URL}/{region_code}.geojson"
            self.stdout.write(f'Descargando región {region_code}: {region_name}...')

            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.stdout.write(f'  Error al descargar región {region_code}: {e}')
                total_errors += 1
                continue
            except json.JSONDecodeError as e:
                self.stdout.write(f'  Error al parsear JSON región {region_code}: {e}')
                total_errors += 1
                continue

            if 'features' not in data:
                self.stdout.write(f'  Formato inesperado en región {region_code}')
                total_errors += 1
                continue

            features = data['features']
            self.stdout.write(f'  Procesando {len(features)} comunas...')

            for feature in features:
                try:
                    props = feature.get('properties', {})
                    geometry = feature.get('geometry', {})

                    # Extraer nombre de la comuna
                    comuna_name = props.get('Comuna', props.get('NAME', props.get('name', '')))
                    if not comuna_name:
                        continue

                    # Usar la región normalizada del código de archivo
                    region_normalized = region_name

                    # Crear o actualizar el límite
                    obj, was_created = GeoRegionBoundary.objects \
                        .update_or_create(
                            name=comuna_name,
                            country='Chile',
                            region=region_normalized,
                            defaults={
                                'geojson': geometry,
                                'osm_id': str(props.get('cod_comuna', '')),
                                'source': 'github',
                            }
                        )

                    if was_created:
                        total_created += 1
                    else:
                        total_updated += 1

                except Exception as e:
                    self.stdout.write(f'  Error procesando {props.get("Comuna", "unknown")}: {e}')
                    total_errors += 1
                    continue

        self.stdout.write(
            f'Resultado final: {total_created} creados, '
            f'{total_updated} actualizados, {total_errors} errores'
        )

    def normalize_region(self, raw_name):
        """Normaliza el nombre de la región al formato del proyecto."""
        return REGION_NAME_MAP.get(raw_name, raw_name)
