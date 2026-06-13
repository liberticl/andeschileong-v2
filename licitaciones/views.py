import json
from decimal import Decimal

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import Licitacion, SyncLog


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def check_and_sync():
    """Verifica si se necesita sincronizar, ejecuta si >24h."""
    last_sync = SyncLog.objects.filter(exitoso=True).first()
    if not last_sync:
        return True
    hours_since = (
        timezone.now() - last_sync.fecha
    ).total_seconds() / 3600
    if hours_since > 24:
        from django.core.management import call_command
        import io
        out = io.StringIO()
        try:
            call_command('sync_licitaciones', '--dias', '7', stdout=out)
        except Exception:
            pass
        return True
    return False


def _apply_filters(queryset, params):
    """Aplica filtros GET a un queryset de licitaciones."""
    estado = params.get('estado')
    region = params.get('region')
    comuna = params.get('comuna')
    year = params.get('year')
    search = params.get('q')

    if estado:
        queryset = queryset.filter(estado=estado)
    if region:
        queryset = queryset.filter(region=region)
    if comuna:
        queryset = queryset.filter(comuna=comuna)
    if year:
        queryset = queryset.filter(fecha_publicacion__year=year)
    if search:
        queryset = queryset.filter(
            Q(nombre__icontains=search) |
            Q(codigo__icontains=search) |
            Q(organismo__icontains=search))
    return queryset


@login_required
def dashboard(request):
    """Dashboard principal con resúmenes y charts."""
    check_and_sync()

    base_qs = Licitacion.objects.filter(activo=True)
    filtered_qs = _apply_filters(base_qs, request.GET)

    # Opciones dinámicas para filtros
    disponibles = Licitacion.objects.filter(activo=True)
    años_disponibles = sorted(
        set(
            disponibles.exclude(fecha_publicacion__isnull=True)
            .values_list('fecha_publicacion__year', flat=True)
        ),
        reverse=True
    )
    regiones_disponibles = sorted(
        set(
            disponibles.exclude(region='', region__isnull=True)
            .values_list('region', flat=True)
        )
    )
    comunas_disponibles = sorted(
        set(
            disponibles.exclude(comuna='', comuna__isnull=True)
            .values_list('comuna', flat=True)
        )
    )

    monto_total = filtered_qs.aggregate(
        total=Sum('monto_estimado'))['total'] or 0

    stats = {
        'total_licitaciones': filtered_qs.count(),
        'por_estado': list(
            filtered_qs.values('estado')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')),
        'por_region': list(
            filtered_qs.exclude(region='', region__isnull=True)
            .values('region')
            .annotate(cantidad=Count('id'), total_monto=Sum('monto_estimado'))
            .order_by('-cantidad')[:10]),
        'por_tipo': list(
            filtered_qs.values('tipo_licitacion')
            .annotate(cantidad=Count('id'))
            .order_by('-cantidad')),
        'monto_total': float(monto_total),
        'monto_total_js': json.dumps(float(monto_total), cls=DecimalEncoder),
        'por_estado_js': json.dumps(
            list(
                filtered_qs.values('estado')
                .annotate(cantidad=Count('id'))
                .order_by('-cantidad')),
            cls=DecimalEncoder),
        'por_region_js': json.dumps(
            list(
                filtered_qs.exclude(region='', region__isnull=True)
                .values('region')
                .annotate(cantidad=Count('id'), total_monto=Sum('monto_estimado'))
                .order_by('-cantidad')[:10]),
            cls=DecimalEncoder),
        'por_tipo_js': json.dumps(
            [
                {**item, 'descripcion': Licitacion.TIPOS.get(
                    item['tipo_licitacion'], item['tipo_licitacion'])}
                for item in list(
                    filtered_qs.values('tipo_licitacion')
                    .annotate(cantidad=Count('id'))
                    .order_by('-cantidad'))
            ],
            cls=DecimalEncoder),
        'licitaciones_recientes': list(
            filtered_qs.order_by('-fecha_publicacion')[:10]),
        'años_disponibles': años_disponibles,
        'regiones_disponibles': regiones_disponibles,
        'comunas_disponibles': comunas_disponibles,
        'filtros': {
            'year': request.GET.get('year', ''),
            'estado': request.GET.get('estado', ''),
            'region': request.GET.get('region', ''),
            'comuna': request.GET.get('comuna', ''),
            'q': request.GET.get('q', ''),
        },
    }

    last_sync = SyncLog.objects.filter(exitoso=True).first()
    stats['last_sync'] = last_sync

    return render(request, 'licitaciones/dashboard.html', stats)


@login_required
def licitaciones_list(request):
    """Tabla paginada de licitaciones con filtros."""
    base_qs = Licitacion.objects.filter(activo=True)
    queryset = _apply_filters(base_qs, request.GET)

    from .forms import FiltroLicitacionesForm
    disponibles = Licitacion.objects.filter(activo=True)
    años = sorted(
        disponibles.exclude(fecha_publicacion__isnull=True)
        .values_list('fecha_publicacion__year', flat=True)
        .distinct(), reverse=True)
    regiones = sorted(
        disponibles.exclude(region='', region__isnull=True)
        .values_list('region', flat=True).distinct())
    comunas = sorted(
        disponibles.exclude(comuna='', comuna__isnull=True)
        .values_list('comuna', flat=True).distinct())
    form = FiltroLicitacionesForm(
        request.GET, años=años, regiones=regiones, comunas=comunas)

    context = {
        'licitaciones': queryset[:100],
        'form': form,
        'total': queryset.count(),
    }
    return render(request, 'licitaciones/licitaciones.html', context)


@login_required
def licitacion_detalle(request, codigo):
    """Detalle de una licitación."""
    licitacion = get_object_or_404(
        Licitacion, codigo=codigo, activo=True)
    return render(
        request, 'licitaciones/detalle.html', {'licitacion': licitacion})


@login_required
def api_stats(request):
    """API JSON para gráficos dinámicos."""
    base_qs = Licitacion.objects.filter(activo=True)

    por_estado = list(
        base_qs.values('estado')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad'))

    por_region = list(
        base_qs.exclude(region='', region__isnull=True)
        .values('region')
        .annotate(
            cantidad=Count('id'),
            total_monto=Sum('monto_estimado'))
        .order_by('-cantidad')[:10])

    por_tipo_raw = list(
        base_qs.values('tipo_licitacion')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad'))
    por_tipo = [
        {**item, 'descripcion': Licitacion.TIPOS.get(
            item['tipo_licitacion'], item['tipo_licitacion'])}
        for item in por_tipo_raw
    ]

    return JsonResponse({
        'por_estado': por_estado,
        'por_region': por_region,
        'por_tipo': por_tipo,
    })
