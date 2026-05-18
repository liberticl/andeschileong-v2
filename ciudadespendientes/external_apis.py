import requests
import geopandas as gpd


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
    data = get_osm_relation(place)
    relation = data[0]
    try:
        url = f'http://polygons.openstreetmap.fr/get_geojson.py?id={relation}&params=0' # noqa
        ans = requests.get(url, timeout=10)
        gdf = gpd.read_file(ans.text)
        gdf = gdf.explode(index_parts=False)
        return [gdf, data[1]]
    except Exception:
        return []
