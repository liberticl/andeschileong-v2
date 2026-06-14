from django.urls import path
from .views import TrafficCountAPIView, contador, contador_model

urlpatterns = [
    path('contador/', contador, name='contador'),
    path('contador/model/', contador_model, name='contador-model'),
]

# API IoT routes (se mantiene en /api/trafico/)
api_urlpatterns = [
    path('trafico/', TrafficCountAPIView.as_view(), name='traffic-api'),
]
