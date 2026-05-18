from django.db import models
from . import choices
import requests
import geopandas as gpd
from django.conf import settings
from django.db.models.signals import pre_save


# TO-DO
# Consulta con todos los OSM ID en overpass-turbo
# [out:json];rel(110808);map_to_area;(way(area)[highway];);out geom; (son~10MB)
# Ver cómo usar esto

class Zone(models.Model):
    """
        Una zona es un lugar al que un usuario puede tener acceso de
        visualización. Esta puede ser un país, una región, una ciudad
        o un espacio particular.
    """

    name = models.CharField(
        "Nombre de la zona", max_length=30, unique=True,
        help_text="Nombre con el que se identifica la zona. Ej: 'Mi región'.")
    zone_type = models.CharField(
        "Tipo", max_length=20, choices=choices.ZONE_TYPES,
        help_text="'Tipo de zona que representa.")
    country = models.CharField(
        "País", max_length=20, choices=choices.COUNTRIES,
        help_text="País al que pertenece la zona.")
    osm_id = models.CharField(
        "ID OSM", max_length=15,
        help_text="Identificador en OpenStreetMaps. Ej: '110808'.")
    coords = models.CharField(
        "Coordenadas", max_length=30,
        help_text="Punto central del polígono. Ej: '-33.0458456,-71.6196749'.")
    mapped_ways = models.JSONField(
        "Vías mapeadas", default=list, blank=True,
        help_text="Vías que están mapeadas en la zona.")
    available_years = models.JSONField(
        "Años disponibles", default=list, blank=True,
        help_text="Años disponibles para esta zona (ej. [2019, 2025]).")
    region = models.CharField(
        "Región/Provincia", max_length=50, choices=choices.REGIONS, blank=True,
        help_text='Región (Chile) o Provincia (Argentina) a la que pertenece esta zona.')

    def __str__(self):
        return f"{self.name} - {self.zone_type}"

    def get_coords(self):
        lat, lon = map(float, self.coords.split(','))
        return (lat, lon)

    def get_osm_data(self, save=False):
        """
            Obtiene OSM ID y coordenadas de un polígono según el
            lugar que representa.
        """
        url = f'https://nominatim.openstreetmap.org/search?q={self.name},%20{self.country}&format=json'  # noqa
        headers = {
            'Referer': settings.CSRF_TRUSTED_ORIGINS[0],
            'User-Agent': 'Urban planning by Andes Chile ONG'
        }
        ans = requests.get(url, headers=headers)
        data = ans.json()

        for element in data:
            if (element['type'] == 'administrative'):
                osmid = element['osm_id']
                center = f"{float(element['lat'])},{float(element['lon'])}"
                self.osm_id = osmid
                self.coords = center
                if (save):
                    self.save(update_fields=['osm_id', 'coords'])
                return [osmid, center]
        print("No se ha encontrado información")
        return []

    def get_mapped_ways(self, osm_id, save=True):
        """
            Obtiene las vías mapeadas según el OSM ID asociado
            a la zona de interés.
        """
        url = 'https://overpass-api.de/api/interpreter'
        query = f'[out:json];rel({osm_id});map_to_area;(way(area)[highway~"cycleway|path|road"];);out geom;' # noqa
        headers = {
            'Referer': settings.CSRF_TRUSTED_ORIGINS[0],
            'User-Agent': 'Urban planning by Andes Chile ONG'
        }
        ans = requests.post(url, headers=headers, data=query)

        if ans.status_code != 200:
            return []
        
        data = ans.json()
        mapped = [el.get('id') for el in data.get('elements', [])]

        self.mapped_ways = mapped
        if (save):
            self.save(update_fields=['mapped_ways'])
        else:
            return mapped

    class Meta:
        verbose_name = u'zona'
        verbose_name_plural = u'Zonas'

    @classmethod
    def before_save(cls, sender, instance, *args, **kwargs):
        # Buscar datos de OSM
        osmid = None
        if (not instance.osm_id or not instance.coords):
            osmid, center = instance.get_osm_data()
        if (not instance.mapped_ways and osmid):
            osm_id = instance.osm_id if instance.osm_id else osmid
            instance.get_mapped_ways(osm_id, save=False)


pre_save.connect(Zone.before_save, sender=Zone)


class StravaData(models.Model):
    """
        Representa un conjunto de datos cargados en MongoDB para
        la plataforma. De aquí el sistema obtiene el listado de
        ciudades y años de datos disponibles.
    """

    on_mongo = models.BooleanField(
        "Cargado en MongoDB",
        help_text="Indica si los datos se encuentran disponibles en MongoDB")
    sector = models.ForeignKey(
        Zone, on_delete=models.CASCADE,
        related_name="sector", verbose_name="Sector"
    )
    year = models.IntegerField(
        "Año", choices=choices.YEARS, default=2024,
        help_text="Año al que pertenece el registro. Ej: 2024.")
    month = models.CharField(
        "Mes", choices=choices.MONTHS, max_length=15, default='Todo el año',
        help_text="Mes al que pertenece el registro. Ej: Enero.")

    def __str__(self):
        return f"{self.sector} - {self.get_month_display()} {self.year}"

    def get_polygon(self, save=True):
        gdf = None
        osm_id = self.sector.osm_id
        url = f'http://polygons.openstreetmap.fr/get_geojson.py?id={osm_id}&params=0'  # noqa
        ans = requests.get(url, timeout=10)
        if (ans.status_code == 200 and save):
            self.save()
            return ans.status_code
        gdf = gpd.read_file(ans.text)
        gdf = gdf.explode(index_parts=False)
        return {
            'success': ans.status_code == 200,
            'polygon': gdf
        }

    def get_sector_coords(self):
        lat, lon = map(float, self.sector.coords.split(','))
        return (lat, lon)

    class Meta:
        verbose_name = u'colección de Strava'
        verbose_name_plural = u'Datos de Strava'
