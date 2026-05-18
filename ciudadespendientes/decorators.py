from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import StravaData
from django.db.models import Prefetch
import time


def user_has_zone_permission(view_func):
    """
        Verifica que el usuario tenga permiso de visualización
        de zonas específicas.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        sectors = request.user.get_user_zones()
        if not sectors:
            raise PermissionDenied(
                "No tienes zonas de visualización asignadas.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def user_has_permission(permissions):
    """
        Verifica que el usuario tenga los permisos requeridos
        para ver un contenido específico
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            can_view = all(request.user.has_permission(
                perm) for perm in permissions)

            if not can_view:
                raise PermissionDenied(
                    "No tienes permisos para ver este contenido.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def calculate_execution_time(func):
    """
    Un decorador que imprime el tiempo de ejecución de la función que decora.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.perf_counter()  # Inicia el contador de alta precisión
        resultado = func(*args, **kwargs)  # Ejecuta la función original
        fin = time.perf_counter()    # Detiene el contador

        duracion = fin - inicio
        print(f"La función '{func.__name__}' tardó {duracion:.4f} segundos en ejecutarse.") # noqa
        return resultado
    return wrapper
