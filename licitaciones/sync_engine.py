import logging
import os
import re
import time
from datetime import date, datetime, timedelta

import requests
from django.utils import timezone
from pytz import timezone as tz
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from licitaciones.models import Licitacion, SyncLog

TZ_SANTIAGO = tz('America/Santiago')

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'AndesChileOng-Sync/1.0 (licitaciones-mercado-publico)',
    'Accept': 'application/json',
}

KEYWORDS_INFRAESTRUCTURA = [
    'ciclovía', 'ciclovia', 'cicloruta', 'ciclo ruta',
    'andén', 'anden', 'peatonal', 'peaton',
    'bicicleta', 'bici', 'ciclismo',
    'seguridad vial', 'mobiliario urbano',
    'infraestructura ciclista', 'vía verde', 'via verde',
    'carril bici', 'sendero ciclista',
    'plan regulador', 'plan seccional', 'pimep', 'imiv',
    ' vial ', 'vialidad'
]

ESTADO_MAP = {
    5: 'publicada',
    6: 'cerrada',
    7: 'desierta',
    8: 'adjudicada',
    18: 'revocada',
    19: 'suspendida',
}

API_BASE = 'https://api.mercadopublico.cl/servicios/v1/publico/'


def _get_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            try:
                dt = datetime.fromisoformat(str(value))
            except (ValueError, TypeError):
                return None
    if timezone.is_naive(dt):
        dt = TZ_SANTIAGO.localize(dt)
    return dt


def _fetch_detalle(codigo, ticket, max_retries=3):
    url = f'{API_BASE}licitaciones.json'
    params = {'codigo': codigo, 'ticket': ticket}
    session = _get_session()
    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            listado = data.get('Listado', [])
            if listado:
                return listado[0]
            if 'CodigoExterno' in data:
                return data
            return None
        except requests.exceptions.SSLError as e:
            logger.warning(f'SSL error {codigo} (attempt {attempt+1}): {e}')
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None
        except requests.exceptions.ConnectionError as e:
            logger.warning(f'Connection error {codigo} (attempt {attempt+1}): {e}')
            if attempt < max_retries - 1:
                time.sleep(3 ** attempt)
            else:
                return None
        except Exception as e:
            logger.warning(f'Error fetching {codigo} (attempt {attempt+1}): {e}')
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None


def _calc_adjudicacion(detail):
    """Calcula total adjudicado desde Items (Cantidad*MontoUnitario).

    Retorna dict con monto_adjudicado, proveedor_adjudicado,
    n_oferentes, url_acta, n_reclamos. Todo None/'' si no hay datos.
    """
    out = {
        'monto_adjudicado': None,
        'proveedor_adjudicado': '',
        'n_oferentes': None,
        'url_acta': '',
        'n_reclamos': None,
    }
    if not isinstance(detail, dict):
        return out
    try:
        out['n_reclamos'] = int(detail.get('CantidadReclamos', 0) or 0)
    except (ValueError, TypeError):
        pass
    adj = detail.get('Adjudicacion')
    if isinstance(adj, dict):
        try:
            n = adj.get('NumeroOferentes')
            out['n_oferentes'] = int(n) if n is not None else None
        except (ValueError, TypeError):
            pass
        out['url_acta'] = adj.get('UrlActa', '') or ''
    items = (detail.get('Items') or {}).get('Listado', []) or []
    total = 0.0
    found = False
    best_prov = ''
    best_monto = 0.0
    for it in items:
        if not isinstance(it, dict):
            continue
        a = it.get('Adjudicacion') or {}
        try:
            cant = float(it.get('Cantidad', 1) or 1)
        except (ValueError, TypeError):
            cant = 1.0
        try:
            mu = a.get('MontoUnitario')
            mu = float(mu) if mu is not None else None
        except (ValueError, TypeError):
            mu = None
        if mu is None:
            continue
        found = True
        linea = cant * mu
        total += linea
        prov = (a.get('NombreProveedor', '') or '').strip()
        if linea >= best_monto and prov:
            best_monto = linea
            best_prov = prov
    if found:
        out['monto_adjudicado'] = round(total, 2)
        out['proveedor_adjudicado'] = best_prov
    return out


def _apply_detail(lic, detail):
    comprador = detail.get('Comprador', {})
    if comprador and isinstance(comprador, dict):
        lic.organismo = comprador.get('NombreOrganismo', '') or ''
        try:
            lic.codigo_organismo = int(
                comprador.get('CodigoOrganismo', 0))
        except (ValueError, TypeError):
            lic.codigo_organismo = None
        lic.region = (
            comprador.get('RegionUnidad', '') or '').strip()
        lic.comuna = (
            comprador.get('ComunaUnidad', '') or '').strip()

    monto = detail.get('MontoEstimado')
    try:
        lic.monto_estimado = float(monto) if monto else None
    except (ValueError, TypeError):
        lic.monto_estimado = None

    fechas = detail.get('Fechas', {}) or {}
    if fechas.get('FechaPublicacion'):
        lic.fecha_publicacion = _parse_datetime(fechas['FechaPublicacion'])
    if fechas.get('FechaCierre'):
        lic.fecha_cierre = _parse_datetime(fechas['FechaCierre'])

    lic.raw_data = detail

    adj = _calc_adjudicacion(detail)
    lic.monto_adjudicado = adj['monto_adjudicado']
    lic.proveedor_adjudicado = adj['proveedor_adjudicado']
    lic.n_oferentes = adj['n_oferentes']
    lic.url_acta = adj['url_acta']
    lic.n_reclamos = adj['n_reclamos']


def _detectar_tipo(codigo):
    if not codigo:
        return ''
    match = re.search(r'-(L[A-Z0-9]+)\d{2}$', codigo)
    if match:
        return match.group(1)
    return ''


def _extract_keywords(nombre):
    nombre_lower = nombre.lower()
    return [
        kw for kw in KEYWORDS_INFRAESTRUCTURA
        if kw.lower() in nombre_lower
    ]


def _map_licitacion(lic):
    organismo = ''
    codigo_organismo = None
    region_unidad = ''
    comuna_unidad = ''
    comprador = lic.get('Comprador', {})
    if comprador and isinstance(comprador, dict):
        organismo = comprador.get('NombreOrganismo', '')
        try:
            codigo_organismo = int(comprador.get('CodigoOrganismo', 0))
        except (ValueError, TypeError):
            codigo_organismo = None
        region_unidad = (comprador.get('RegionUnidad', '') or '').strip()
        comuna_unidad = (comprador.get('ComunaUnidad', '') or '').strip()

    estado_code = lic.get('CodigoEstado', 0)
    try:
        estado_code = int(estado_code)
    except (ValueError, TypeError):
        estado_code = 0
    estado = ESTADO_MAP.get(estado_code, 'publicada')

    monto = lic.get('MontoEstimado')
    try:
        monto = float(monto) if monto else None
    except (ValueError, TypeError):
        monto = None

    tipo = lic.get('Tipo', '')
    if not tipo:
        tipo = _detectar_tipo(lic.get('CodigoExterno', ''))

    fechas = lic.get('Fechas', {}) or {}
    fecha_pub = fechas.get('FechaPublicacion') or lic.get('FechaPublicacion')
    fecha_cierre = fechas.get('FechaCierre') or lic.get('FechaCierre')

    adj = _calc_adjudicacion(lic)

    return {
        'nombre': lic.get('Nombre', ''),
        'organismo': organismo,
        'codigo_organismo': codigo_organismo,
        'monto_estimado': monto,
        'monto_adjudicado': adj['monto_adjudicado'],
        'proveedor_adjudicado': adj['proveedor_adjudicado'],
        'n_oferentes': adj['n_oferentes'],
        'url_acta': adj['url_acta'],
        'n_reclamos': adj['n_reclamos'],
        'moneda': lic.get('Moneda', 'CLP'),
        'estado': estado,
        'fecha_cierre': _parse_datetime(fecha_cierre),
        'fecha_publicacion': _parse_datetime(fecha_pub),
        'tipo_licitacion': tipo[:5] if tipo else '',
        'comuna': comuna_unidad,
        'region': region_unidad,
        'palabras_clave': _extract_keywords(
            lic.get('Nombre', '')),
        'raw_data': lic,
    }


def run_sync(dias=7, ticket=None):
    ticket = ticket or os.environ.get('MERCADO_PUBLICO_TICKET')
    if not ticket:
        raise ValueError("No MERCADO_PUBLICO_TICKET configured")

    start_time = time.time()
    consultadas = 0
    filtradas = 0
    nuevas = 0
    actualizadas = 0
    errores = 0
    detalles_ok = 0

    keywords_lower = [k.lower() for k in KEYWORDS_INFRAESTRUCTURA]
    session = _get_session()

    for i in range(dias):
        fecha = date.today() - timedelta(days=i)
        fecha_str = fecha.strftime('%d%m%Y')
        url = f'{API_BASE}licitaciones.json'
        params = {'fecha': fecha_str, 'ticket': ticket}

        try:
            response = session.get(url, params=params, timeout=45)
            response.raise_for_status()
            data = response.json()
            licitaciones = data.get('Listado', [])
            consultadas += len(licitaciones)

            for lic in licitaciones:
                nombre = lic.get('Nombre', '').lower()
                if not any(k in nombre for k in keywords_lower):
                    continue

                filtradas += 1
                codigo = lic['CodigoExterno']

                detail = _fetch_detalle(codigo, ticket)
                if detail:
                    detalles_ok += 1
                    merged = {**lic, **detail}
                else:
                    merged = lic
                    errores += 1

                mapped = _map_licitacion(merged)
                obj, created = (
                    Licitacion.objects
                    .update_or_create(
                        codigo=codigo,
                        defaults=mapped)
                )
                if created:
                    nuevas += 1
                else:
                    actualizadas += 1

                time.sleep(1.0)

        except Exception as e:
            errores += 1
            logger.error(f'Error en fecha {fecha_str}: {e}')

    incompletas = Licitacion.objects.filter(
        activo=True, organismo='')
    if incompletas.exists():
        logger.info(
            f'Re-fetching {incompletas.count()} '
            f'licitaciones sin organismo...')
        for lic in incompletas:
            try:
                detail = _fetch_detalle(lic.codigo, ticket)
                if detail:
                    _apply_detail(lic, detail)
                    lic.save()
                time.sleep(1.0)
            except Exception as e:
                logger.warning(f'Error re-fetch {lic.codigo}: {e}')

    duracion = time.time() - start_time
    SyncLog.objects.create(
        licitaciones_consultadas=consultadas,
        licitaciones_filtradas=filtradas,
        licitaciones_nuevas=nuevas,
        licitaciones_actualizadas=actualizadas,
        errores=errores,
        duracion_segundos=duracion,
    )

    return {
        'nuevas': nuevas,
        'actualizadas': actualizadas,
        'filtradas': filtradas,
        'consultadas': consultadas,
        'detalles_ok': detalles_ok,
        'errores': errores,
        'duracion': duracion,
    }
