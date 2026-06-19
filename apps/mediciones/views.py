from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import gzip
import json
import logging
import os
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .auth import JWTAuthentication
from rest_framework import status
from .serializers import TrafficCountSerializer, TrafficCountBatchSerializer
from .models import Device, TrafficCount
from ciudadespendientes.external_apis import reverse_geocode, parse_device_name

logger = logging.getLogger(__name__)


def contador(request):
    return render(request, 'mediciones/contador.html', {
        'sync_interval': settings.TRAFFICO_SYNC_INTERVAL_MINUTES,
    })


def contador_model(request):
    size = request.GET.get('size', '640')
    if size == '320':
        model_file = 'yolo26n-320.onnx'
    else:
        model_file = 'yolo26n.onnx'
    model_path = os.path.join(settings.BASE_DIR, 'apps', 'mediciones', 'static', 'mediciones', 'models', model_file)
    return FileResponse(open(model_path, 'rb'), content_type='application/octet-stream')


@method_decorator(csrf_exempt, name='dispatch')
class DeviceRegisterView(APIView):
    """
    Auto-registro de dispositivos. No requiere autenticación.
    Recibe un fingerprint del navegador, crea o retorna el device existente.
    """
    authentication_classes = []

    def post(self, request):
        fingerprint = request.data.get('fingerprint', '').strip()
        if not fingerprint:
            return Response(
                {'status': False, 'errors': {'fingerprint': ['Este campo es obligatorio.']}},
                status=status.HTTP_400_BAD_REQUEST)

        user_agent = request.data.get('user_agent', '')
        coords = request.data.get('coords', '')

        device = Device.objects.filter(fingerprint=fingerprint).first()
        created = device is None

        if created:
            # Generar nombre legible
            name = ''
            if coords:
                parts = coords.split(',')
                if len(parts) == 2:
                    try:
                        name = reverse_geocode(float(parts[0]), float(parts[1]))
                    except (ValueError, TypeError):
                        pass
            if not name:
                name = parse_device_name(user_agent)

            device = Device.objects.create(
                fingerprint=fingerprint,
                name=name,
                coords=coords,
                user_agent=user_agent,
                is_active=True,
            )
        else:
            device.last_seen = timezone.now()
            updates = ['last_seen']
            if coords and not device.coords:
                device.coords = coords
                updates.append('coords')
            if user_agent and not device.user_agent:
                device.user_agent = user_agent
                updates.append('user_agent')
            device.save(update_fields=updates)

        return Response({
            'status': True,
            'token': device.token,
            'device_name': device.name,
            'device_id': device.pk,
            'created': created,
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceNameUpdateView(APIView):
    """
    Permite renombrar un dispositivo. Requiere JWT.
    """
    authentication_classes = [JWTAuthentication]

    def patch(self, request):
        device = request.user
        if not device or not device.is_active:
            return Response(
                {'status': False, 'errors': {'inactive': ['El dispositivo no está activo']}},
                status=status.HTTP_403_FORBIDDEN)

        name = request.data.get('name', '').strip()
        if not name:
            return Response(
                {'status': False, 'errors': {'name': ['Este campo es obligatorio.']}},
                status=status.HTTP_400_BAD_REQUEST)

        device.name = name
        device.save(update_fields=['name'])

        return Response({
            'status': True,
            'device_name': device.name,
        }, status=status.HTTP_200_OK)


def _decode_request_body(request):
    """
    Return parsed JSON from the request body, transparently handling
    gzip-compressed payloads (Content-Encoding: gzip).
    """
    content_encoding = request.headers.get('Content-Encoding', '')
    if 'gzip' in content_encoding.lower():
        try:
            raw = gzip.decompress(request.body)
            return json.loads(raw.decode('utf-8'))
        except Exception as exc:
            raise ValueError(f"Payload gzip inválido: {exc}") from exc
    # Fall back to DRF's already-parsed data
    return request.data


def _is_duplicate(device, datetime_value, window_seconds=1):
    """
    Return True if a TrafficCount for this device already exists within
    *window_seconds* of *datetime_value*.  Used to drop accidental
    double-submissions from the frontend.
    """
    if not datetime_value:
        return False
    try:
        window = timedelta(seconds=window_seconds)
        return TrafficCount.objects.filter(
            device=device,
            datetime__gte=datetime_value - window,
            datetime__lte=datetime_value + window,
        ).exists()
    except Exception:
        return False


class TrafficCountAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        device = request.user
        if (not device) or (device and not device.is_active):
            err = "El dispositivo no está activo"
            return Response(
                {'status': False, 'errors': {"inactive": [err]}},
                status=status.HTTP_403_FORBIDDEN)

        try:
            data = _decode_request_body(request)
        except ValueError as exc:
            return Response(
                {'status': False, 'errors': {'payload': [str(exc)]}},
                status=status.HTTP_400_BAD_REQUEST)

        serializer = TrafficCountSerializer(
            data=data, context={'request': request})

        if serializer.is_valid():
            dt = serializer.validated_data.get('datetime')
            if _is_duplicate(device, dt):
                logger.debug(
                    "Duplicate TrafficCount dropped for device=%s dt=%s",
                    device.pk, dt)
                return Response(
                    {'status': True, 'deduplicated': True},
                    status=status.HTTP_200_OK)

            serializer.save()
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            return Response(
                {'status': True, 'data': serializer.data},
                status=status.HTTP_201_CREATED)

        return Response(
            {'status': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class TrafficCountBatchAPIView(APIView):
    """
    Accepts a JSON body of the form::

        {"records": [
            {"datetime": "...", "car_count": 3, ...},
            ...
        ]}

    Optionally gzip-compressed (Content-Encoding: gzip).
    Saves each record individually, skipping duplicates.
    Returns a summary: {"status": true, "saved": N, "skipped": N}
    """
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        device = request.user
        if (not device) or (device and not device.is_active):
            err = "El dispositivo no está activo"
            return Response(
                {'status': False, 'errors': {"inactive": [err]}},
                status=status.HTTP_403_FORBIDDEN)

        try:
            data = _decode_request_body(request)
        except ValueError as exc:
            return Response(
                {'status': False, 'errors': {'payload': [str(exc)]}},
                status=status.HTTP_400_BAD_REQUEST)

        batch_serializer = TrafficCountBatchSerializer(
            data=data, context={'request': request})

        if not batch_serializer.is_valid():
            return Response(
                {'status': False, 'errors': batch_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST)

        records = batch_serializer.validated_data['records']
        saved = 0
        skipped = 0

        for record_data in records:
            dt = record_data.get('datetime')
            if _is_duplicate(device, dt):
                logger.debug(
                    "Batch duplicate dropped for device=%s dt=%s",
                    device.pk, dt)
                skipped += 1
                continue

            record_serializer = TrafficCountSerializer(
                data=record_data, context={'request': request})
            if record_serializer.is_valid():
                record_serializer.save()
                saved += 1
            else:
                logger.warning(
                    "Invalid record in batch for device=%s: %s",
                    device.pk, record_serializer.errors)
                skipped += 1

        if saved > 0:
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])

        return Response(
            {'status': True, 'saved': saved, 'skipped': skipped},
            status=status.HTTP_201_CREATED if saved > 0 else status.HTTP_200_OK)
