from django.urls import path
from .views import TrafficCountAPIView

urlpatterns = [
    path('trafico/', TrafficCountAPIView.as_view(), name='traffic-api'),
]
