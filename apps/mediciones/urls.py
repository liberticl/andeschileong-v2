from django.urls import path
from .views import TrafficCountAPIView, DeviceRegisterView, DeviceNameUpdateView, contador, contador_model, contador_externo

urlpatterns = [
    path('contador/', contador, name='contador'),
    path('contador/model/', contador_model, name='contador-model'),
    path('contador-externo/', contador_externo, name='contador-externo'),
]

# API IoT routes (se mantiene en /api/trafico/)
api_urlpatterns = [
    path('trafico/', TrafficCountAPIView.as_view(), name='traffic-api'),
    path('trafico/register/', DeviceRegisterView.as_view(), name='traffic-register'),
    path('trafico/device/', DeviceNameUpdateView.as_view(), name='traffic-device-name'),
]
