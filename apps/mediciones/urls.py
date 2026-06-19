from django.urls import path
from .views import (
    TrafficCountAPIView, TrafficCountBatchAPIView,
    DeviceRegisterView, DeviceNameUpdateView,
    contador, contador_model,
)

urlpatterns = [
    path('contador/', contador, name='contador'),
    path('contador/model/', contador_model, name='contador-model'),
]

# API IoT routes (se mantiene en /api/trafico/)
api_urlpatterns = [
    path('trafico/', TrafficCountAPIView.as_view(), name='traffic-api'),
    path('trafico/batch/', TrafficCountBatchAPIView.as_view(), name='traffic-api-batch'),
    path('trafico/register/', DeviceRegisterView.as_view(), name='traffic-register'),
    path('trafico/device/', DeviceNameUpdateView.as_view(), name='traffic-device-name'),
]
