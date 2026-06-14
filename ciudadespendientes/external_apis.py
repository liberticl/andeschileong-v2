import requests
import re
import geopandas as gpd
from .models import GeoRegionBoundary
from shapely.geometry import shape

NOMINATIM_HEADERS = {
    'Referer': 'https://andeschileong.cl',
    'User-Agent': 'Urban planning by Andes Chile ONG'
}


def reverse_geocode(lat, lng):
    """
    Reverse geocoding usando Nominatim. Devuelve un string legible
    como 'Providencia, Región Metropolitana' o '' si falla.
    """
    try:
        url = f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&zoom=14'
        resp = requests.get(url, headers=NOMINATIM_HEADERS, timeout=5)
        data = resp.json()
        addr = data.get('address', {})
        parts = []
        for key in ['neighbourhood', 'suburb', 'city_district', 'city', 'town', 'municipality']:
            if key in addr:
                parts.append(addr[key])
                break
        if 'state' in addr:
            parts.append(addr['state'])
        return ', '.join(parts) if parts else data.get('display_name', '').split(',')[0]
    except Exception:
        return ''


def parse_device_name(user_agent):
    """
    Extrae navegador y SO del User-Agent string.
    Ejemplos: 'Chrome 120 / Linux', 'Safari / iOS 17', 'Firefox / Windows'
    """
    ua = user_agent or ''

    browser = ''
    m = re.search(r'Chrome/(\d+)', ua)
    if m:
        browser = f'Chrome {m.group(1)}'
    else:
        m = re.search(r'Firefox/(\d+)', ua)
        if m:
            browser = f'Firefox {m.group(1)}'
        else:
            m = re.search(r'Safari/', ua)
            if m and 'Chrome' not in ua:
                browser = 'Safari'
            else:
                m = re.search(r'Edg/(\d+)', ua)
                if m:
                    browser = f'Edge {m.group(1)}'

    os_name = ''
    if 'Windows' in ua:
        os_name = 'Windows'
    elif 'Mac OS X' in ua:
        os_name = 'macOS'
    elif 'Linux' in ua:
        os_name = 'Linux'
    elif 'Android' in ua:
        os_name = 'Android'
    elif 'iPhone' in ua or 'iPad' in ua:
        os_name = 'iOS'

    parts = [p for p in [browser, os_name] if p]
    return ' / '.join(parts) if parts else 'Dispositivo desconocido'


def get_osm_relation(place: str):
    url = f'https://nominatim.openstreetmap.org/search?q={place}&format=json'
    ans = requests.get(url, headers=NOMINATIM_HEADERS)
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
