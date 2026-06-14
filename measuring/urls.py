from django.urls import path
from .views import TrafficCountAPIView, counter

urlpatterns = [
    path('counter/', counter, name='counter'),
    path('trafico/', TrafficCountAPIView.as_view(), name='traffic-api'),
]
