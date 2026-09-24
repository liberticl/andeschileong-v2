from django.conf import settings


def carto(request):
    """Expone la API key de CARTO Basemaps a todos los templates."""
    return {
        'CARTO_API_KEY': settings.CARTO_API_KEY,
    }
