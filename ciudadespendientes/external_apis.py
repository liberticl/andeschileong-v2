import requests
import geopandas as gpd
from .models import GeoRegionBoundary
from shapely.geometry import shape


def get_osm_relation(place: str):
    url = f'https://nominatim.openstreetmap.org/search?q={place}&format=json'
    headers = {
        'Referer': 'https://andeschileong.cl',
        'User-Agent': 'Urban planning by Andes Chile ONG'
    }
    ans = requests.get(url, headers=headers)
    data = ans.json()

    for element in data:
        if (element['type'] == 'administrative'):
            return [element['osm_id'],
                    (float(element['lat']), float(element['lon']))]

    return None


def get_place_polygon(place):
    """
    Obtiene el polígono de un lugar. Primero consulta la BD local,
    si no existe busca en OpenStreetMap.
    """
    # 1. Intentar obtener desde la BD local
    local_result = get_local_polygon(place)
    if local_result:
        return local_result

    # 2. Si no está en local, buscar en OSM
    data = get_osm_relation(place)
    if not data:
        return []

    relation = data[0]
    try:
        url = f'http://polygons.openstreetmap.fr/get_geojson.py?id={relation}&params=0'  # noqa
        ans = requests.get(url, timeout=10)
        gdf = gpd.read_file(ans.text)
        gdf = gdf.explode(index_parts=False)
        return [gdf, data[1]]
    except Exception:
        return []


def get_local_polygon(place_name, country='Chile'):
    """
    Busca el polígono en la BD local por nombre de lugar.
    Retorna [GeoDataFrame, (lat, lon)] o None si no existe.
    """
    # Buscar por nombre exacto
    boundary = GeoRegionBoundary.objects.filter(
        name__iexact=place_name,
        country=country
    ).first()

    if not boundary:
        # Buscar por coincidencia parcial
        boundary = GeoRegionBoundary.objects.filter(
            name__icontains=place_name,
            country=country
        ).first()

    if not boundary:
        return None

    # Convertir GeoJSON a GeoDataFrame
    geom = shape(boundary.geojson)
    gdf = gpd.GeoDataFrame([{'geometry': geom}], crs="epsg:4326")
    gdf = gdf.explode(index_parts=False)

    # Extraer coordenadas del centro (si están disponibles en el GeoJSON)
    centroid = geom.centroid
    center_coords = (centroid.y, centroid.x)  # (lat, lon)

    return [gdf, center_coords]
