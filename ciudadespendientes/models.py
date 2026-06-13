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
        "Años disponibles (deprecated)", default=list, blank=True,
        help_text="DEPRECATED: Los años se obtienen desde StravaData. Este campo ya no se usa.")
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


class GeoRegionBoundary(models.Model):
    """
        Almacena los polígonos geográficos de comunas y regiones de Chile.
        Permite consultar límites locales antes de ir a OSM.
    """
    name = models.CharField(
        "Nombre", max_length=100,
        help_text="Nombre de la comuna o región.")
    region = models.CharField(
        "Región", max_length=50, choices=choices.REGIONS, blank=True,
        help_text="Región a la que pertenece.")
    country = models.CharField(
        "País", max_length=20, choices=choices.COUNTRIES, default='Chile',
        help_text="País al que pertenece.")
    osm_id = models.CharField(
        "ID OSM", max_length=15, blank=True,
        help_text="Identificador OpenStreetMap para referencia.")
    geojson = models.JSONField(
        "GeoJSON", help_text="Geometría del polígono en formato GeoJSON.")
    source = models.CharField(
        "Fuente", max_length=50, default='manual',
        help_text="Fuente de los datos: manual, catastro, osm, etc.")
    last_updated = models.DateTimeField(
        "Última actualización", auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.region} ({self.country})"

    class Meta:
        verbose_name = u'límite geográfico'
        verbose_name_plural = u'Límites Geográficos'
        unique_together = ('name', 'country', 'region')

    def get_geometry(self):
        """Retorna la geometría como GeoDataFrame de GeoPandas."""
        import geopandas as gpd
        from shapely.geometry import shape
        geom = shape(self.geojson)
        return gpd.GeoDataFrame([{'geometry': geom}], crs="epsg:4326")


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
        """
        Obtiene el polígono de la zona. Primero consulta la BD local,
        si no existe busca en OpenStreetMap.
        """
        # 1. Intentar obtener desde la BD local (GeoRegionBoundary)
        local_boundary = self.get_local_boundary()
        if local_boundary:
            gdf = local_boundary.get_geometry()
            gdf = gdf.explode(index_parts=False)
            if save:
                self.save()
            return {'success': True, 'polygon': gdf, 'source': 'local'}

        # 2. Si no está en local, buscar en OSM
        osm_id = self.sector.osm_id
        url = f'http://polygons.openstreetmap.fr/get_geojson.py?id={osm_id}&params=0'  # noqa
        try:
            ans = requests.get(url, timeout=10)
            if ans.status_code != 200:
                return {'success': False, 'polygon': None, 'source': 'osm_failed'}
            if save:
                self.save()
            gdf = gpd.read_file(ans.text)
            gdf = gdf.explode(index_parts=False)
            return {'success': True, 'polygon': gdf, 'source': 'osm'}
        except requests.RequestException:
            return {'success': False, 'polygon': None, 'source': 'osm_error'}

    def get_local_boundary(self):
        """
        Busca el polígono en la BD local por nombre de comuna y región.
        Retorna el GeoRegionBoundary o None si no existe.
        """
        from ciudadespendientes.models import GeoRegionBoundary
        sector = self.sector

        # Buscar por nombre exacto de comuna
        boundary = GeoRegionBoundary.objects.filter(
            name__iexact=sector.name,
            country=sector.country
        ).first()

        if boundary:
            return boundary

        # Si no encuentra por nombre exacto, buscar por región si es zona regional
        if sector.zone_type == 'Zona Regional' and sector.region:
            boundary = GeoRegionBoundary.objects.filter(
                region__iexact=sector.region,
                country=sector.country
            ).first()
            if boundary:
                return boundary

        # Buscar por coincidencia parcial del nombre
        boundary = GeoRegionBoundary.objects.filter(
            name__icontains=sector.name,
            country=sector.country
        ).first()

        return boundary

    def get_sector_coords(self):
        lat, lon = map(float, self.sector.coords.split(','))
        return (lat, lon)

    class Meta:
        verbose_name = u'colección de Strava'
        verbose_name_plural = u'Datos de Strava'
