from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from django.conf import settings
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from .auth import JWTAuthentication
from rest_framework import status
from .serializers import TrafficCountSerializer


def counter(request):
    with open('measuring/templates/measuring/counter.html', 'r') as f:
        return HttpResponse(f.read(), content_type='text/html')


def counter_model(request):
    size = request.GET.get('size', '640')
    if size == '320':
        model_file = 'yolo26n-320.onnx'
    else:
        model_file = 'yolo26n.onnx'
    model_path = os.path.join(settings.BASE_DIR, 'measuring', 'static', 'measuring', 'models', model_file)
    return FileResponse(open(model_path, 'rb'), content_type='application/octet-stream')


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

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'status': serializer.is_valid(), 'data': serializer.data},
                status=status.HTTP_201_CREATED)

        return Response(
            {'status': serializer.is_valid(), 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST)
