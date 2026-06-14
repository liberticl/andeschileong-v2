import re
import copy
import requests
import pandas as pd
import geopandas as gpd
from .mongodb import middle_points_aggregate, points_inside
from zipfile import ZipFile
from bs4 import BeautifulSoup
from pymongo import MongoClient, UpdateOne
from shapely.geometry import Polygon, LineString
# from .decorators import calculate_execution_time
from andeschileong.settings import (
    MONGO_DB, MONGO_CP_DB, CP_STRAVA_COLLECTION,
    DECKGL_VERSION)


# Creates the mongodb files to upload
def create_features(geodata, max=10):
    features = []
    for feature in geodata.iterfeatures():
        prop = feature.pop('properties', None)
        if prop:
            feature.update(prop)
        feature.pop('id', None)
        feature.pop('type', None)
        feature.pop('edge_uid', None)
        feature.pop('osm_reference_id', None)
        features.append(feature)

    return features


# Get data from Strava's ZIP file.
# - SHP file for geometry objects
# - CSV file for getting Strava info
def strava_to_mongo(path, collection):
    yield f'Extrayendo los datos de {path.split("/")[-1]}...'

    with ZipFile(path, 'r') as zip:
        files = zip.infolist()
        shpfile = [file.filename for file in files if 'shp' in file.filename][0] # noqa
        csvfile = [file for file in files if 'csv' in file.filename][0]

        geodata = gpd.read_file(path + '!' + shpfile, )
        with zip.open(csvfile) as csv:
            data = pd.read_csv(csv, low_memory=False)

    yield 'Generando elementos para subir a mongodb...'
    merged_df = pd.merge(geodata, data,
                         how='inner', left_on='edgeUID', right_on='edge_uid')

    features = create_features(merged_df)
    yield f'Insertando {len(features)} elementos en mongodb...'
    collection.insert_many(features, ordered=False)
    yield 'Inserción base completada.'


# Get middle point for all lines
def create_middle_points(collection):
    yield 'Ejecutando pipeline de agregación para puntos medios...'
    pipeline = middle_points_aggregate
    cursor = collection.aggregate(pipeline)
    data = list(cursor)

    yield f'Calculando y preparando actualización para {len(data)} trayectos...'
    update_operation = [
        {
            'filter': {'_id': result['_id']},
            'update': {'$set': {'middlePoint': result['middlePoint']}}
        }
        for result in data
    ]

    collection.bulk_write([UpdateOne(**op) for op in update_operation])
    yield 'Puntos medios guardados en masa de forma exitosa.'


# Get middle point of city reference
def get_middle_point(references):
    references_sum = [0, 0]

    for ref in references:
        references_sum = [x + y for x, y in zip(references_sum, ref)]

    return tuple([element / len(references) for element in references_sum])


def get_ride_from_mongo(city_bounds, years, collection, osm_ids=[]):
    full_coords = []
    for bounds in city_bounds:
        coords = list(Polygon(bounds).exterior.coords)
        coords = [[round(x, 6), round(y, 6)] for x, y in coords]
        coords = coords + [coords[0]]
        seen = set()
        deduped = []
        for i, pt in enumerate(coords):
            key = (pt[0], pt[1])
            if key not in seen or i == len(coords) - 1:
                seen.add(key)
                deduped.append(pt)
        full_coords.append([deduped])

    pipeline = copy.deepcopy(points_inside)
    match_stage = pipeline[0]['$match']
    match_stage['year']['$in'] = years
    match_stage['middlePoint']['$geoIntersects']['$geometry']['coordinates'] = full_coords

    return list(collection.aggregate(pipeline))


def process_ride_data(mongodata):
    df = pd.DataFrame(list(mongodata))
    if df.empty:
        return df, []

    # Simplificación de geometrías para mejorar rendimiento de renderizado
    # Tolerancia de 0.00001 (~1 metro) para no perder precisión visual
    def simplify_coords(coords):
        if len(coords) < 3:
            return coords
        line = LineString(coords)
        simplified = line.simplify(0.00001, preserve_topology=True)
        return list(simplified.coords)

    df['coordinates'] = df['coordinates'].apply(simplify_coords)

    return df, df['trips'].tolist()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_location_from_ip(ip):
    url = f"https://ipinfo.io/{ip}/json"
    try:
        r = requests.get(url)
        data = r.json() if r.status_code == 200 else {}
        is_success = r.status_code == 200
    except requests.RequestException:
        data = {}
        is_success = False

    return {
        'sucess': is_success,
        'bogon': data.get('bogon', False),
        'loc': data.get('loc', '-33.0498108,-71.6213084')
    }


def upload_data(zip_path='data.zip'):
    yield "Estableciendo conexión con MongoDB..."
    client = MongoClient(MONGO_DB)
    db = client[MONGO_CP_DB]
    collection = db[CP_STRAVA_COLLECTION]

    for msg in strava_to_mongo(zip_path, collection):
        yield msg

    for msg in create_middle_points(collection):
        yield msg

    yield "¡Finalizado!"
    client.close()


def get_city_data(polygon):
    gdf_city = polygon.set_crs("epsg:4326")
    gdf_city = gdf_city.to_crs(crs=3857)
    gdf_city['area'] = gdf_city['geometry'].area
    data = gdf_city[gdf_city['area'] == gdf_city['area'].max()]
    data = data.to_crs(crs=4326).to_dict()
    return data['geometry'][0]


def change_gl_version(url: str):
    match = re.search(r'@~(\d+\.\d+\.\*)', url)
    if match:
        return url.replace(match.group(1), DECKGL_VERSION)
    else:
        return url


def get_html(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    scripts = list(soup.find_all('script'))
    links = list(soup.find_all('link'))
    html = links + scripts[:2]
    headers = [change_gl_version(str(h)) for h in html]
    gl_script = scripts[-1].string
    deckgl = f'\n<div id="deck-container"></div>\n<script>{gl_script}</script>'  # noqa
    return '\n'.join(headers), deckgl
