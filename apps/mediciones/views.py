from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from .auth import JWTAuthentication
from rest_framework import status
from .serializers import TrafficCountSerializer
from .models import Device
from ciudadespendientes.external_apis import reverse_geocode, parse_device_name


def contador(request):
    return render(request, 'mediciones/contador.html', {
        'sync_interval': settings.TRAFFICO_SYNC_INTERVAL_MINUTES,
    })


def contador_externo(request):
    return render(request, 'mediciones/contador_externo.html', {
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


class TrafficCountAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = TrafficCountSerializer(
            data=request.data, context={'request': request})

        device = request.user
        if (not device) or (device and not device.is_active):
            err = "El dispositivo no está activo"
            return Response(
                {'status': False, 'errors': {"inactive": [err]}},
                status=status.HTTP_403_FORBIDDEN)

        device.last_seen = timezone.now()
        device.save(update_fields=['last_seen'])

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'status': serializer.is_valid(), 'data': serializer.data},
                status=status.HTTP_201_CREATED)

        return Response(
            {'status': serializer.is_valid(), 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST)
