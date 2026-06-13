import numpy as np
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from .classifier import get_statistics
from .utils import (get_middle_point, get_city_data, get_html,
                    get_ride_from_mongo, process_ride_data,
                    get_client_ip, get_location_from_ip)
import pydeck as pdk
from .models import StravaData
from .decorators import user_has_zone_permission, user_has_permission

collection = settings.STRAVA_COLLECTION
LAYER_COLORS = settings.LAYERS
GREEN = settings.GREEN
ALLOWED_YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def welcome(request):
    user = request.user if request.user.is_authenticated else None
    organization = user.get_first_organization() if user else None
    permissions = [p.code for p in user.get_user_permissions()] if user else []
    
    client_ip = get_client_ip(request)
    location_data = get_location_from_ip(client_ip)
    
    return render(request, "ciudadespendientes/welcome.html",
                  {'user': user,
                   'organization': organization,
                   'permissions': permissions,
                   'loc': location_data.get('loc')})


@login_required
@user_has_zone_permission
def find(request):
    if request.method == "POST":
        years = request.POST.getlist("periodo")
        cities = request.POST.getlist("comunas")

        return redirect(reverse("show_data") + f"?periodo={','.join(years)}&comunas={','.join(cities)}")  # noqa

    sectors = request.user.get_user_zones()

    return render(request, "ciudadespendientes/buscar.html",
                  {'periodo': ALLOWED_YEARS,
                   'comunas': sectors,
                   'organization': request.user.get_first_organization()})


@login_required
@user_has_zone_permission
@user_has_permission(permissions=['view_strava_data'])
def show_data(request):
    user_sectors = request.user.get_user_zones()
    user_sector_names = [s['name'] for s in user_sectors]

    try:
        years = [int(year) for year in request.GET["periodo"].split(',')]
        cities = [city for city in request.GET["comunas"].split(',') if city in user_sector_names] # noqa
    except Exception:
        return redirect('error_404')

    if (not cities or not years):
        return redirect('error_403')

    sectors = StravaData.objects.filter(
        sector__name__in=cities, year__in=years).select_related('sector')

    unique_polygons = {}
    all_bounds = []
    all_references = []
    for s in sectors:
        sector_id = s.sector_id
        if sector_id not in unique_polygons:
            polygon = s.get_polygon(save=False)
            if (polygon['success']):
                unique_polygons[sector_id] = get_city_data(polygon['polygon'])
            else:
                unique_polygons[sector_id] = None
        
        if unique_polygons[sector_id]:
            if unique_polygons[sector_id] not in all_bounds:
                all_bounds.append(unique_polygons[sector_id])
            
        all_references.append(s.get_sector_coords())

    center = get_middle_point(all_references)
    if not all_bounds:
        return redirect('error_404')
    m, s = color_ride_map(all_bounds, center, years,
                          collection, anual=False)

    html_map = m.to_html(as_string=True)
    headers, deckgl = get_html(html_map)
    stats = [round(x) for x in s]
    return render(request, 'ciudadespendientes/mapa.html', {
                  'headers': headers,
                  'deckgl': deckgl,
                  'query_string': request.GET.urlencode(),
                  'layers': [
                      {
                          'id': 'green',
                          'visible': 'unchecked',
                          'label': 'Flujo bajo',
                          'stats': f"Menos que {stats[0] - 1} viajes"
                      },
                      {
                          'id': 'orange',
                          'visible': 'checked',
                          'label': 'Flujo medio',
                          'stats': f"Entre {stats[0]} y {stats[1] - 1} viajes"
                      },
                      {
                          'id': 'red',
                          'visible': 'checked',
                          'label': 'Flujo alto',
                          'stats': f"Más que {stats[1]} viajes"
                      }
                  ]
                  })


def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_403(request, exception=None):
    return render(request, '403.html', status=403)


def create_layer(data):
    is_visible = False if data['color_txt'] == GREEN else True
    return pdk.Layer(
        "PathLayer",
        data=[],
        id=data['color_txt'],
        get_path="coordinates",
        get_color=data['color'],
        get_width=data['width'],
        width_min_pixels=2,
        pickable=True,
        visible=is_visible,
        name=data['label'],
    )


def prepare_map(center):
    view_state = pdk.ViewState(
        latitude=center[0],
        longitude=center[1],
        zoom=13,
        pitch=20,
        bearing=0,
    )

    layers = {}
    for layer, data in LAYER_COLORS.items():
        layers[layer] = create_layer(data)

    return (view_state, layers)


def color_ride_map(city_bounds, center, years, collection, factor=1, anual=False):
    view_state, layers = prepare_map(center)
    mongodata = get_ride_from_mongo(city_bounds, years, collection)
    df, trip_count = process_ride_data(mongodata)

    if df.empty:
        mapa = pdk.Deck(layers=[], initial_view_state=view_state)
        return mapa, (0, 0)

    stats = get_statistics(trip_count, years)
    mean, std = stats
    
    # Cálculo vectorial de clasificaciones
    num_years = len(years) if anual else 1
    trips_per_year = (df['trips'] / factor) / num_years
    
    # Creamos una columna de clasificación usando np.select (mucho más rápido que un apply)
    conditions = [
        (trips_per_year > mean + std),
        (trips_per_year > mean)
    ]
    choices = ['red', 'orange']
    df['color_group'] = np.select(conditions, choices, default='green')

    # Asignación masiva a las capas
    for color, layer in layers.items():
        layer.data = df[df['color_group'] == color]

    mapa = pdk.Deck(
        layers=list(layers.values()),
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={"text": "Viajes totales: {trips}"},
    )

    return mapa, stats
