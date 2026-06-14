from django.urls import path
from .views import TrafficCountAPIView, counter, counter_model

urlpatterns = [
    path('counter/', counter, name='counter'),
    path('counter/model/', counter_model, name='counter-model'),
    path('trafico/', TrafficCountAPIView.as_view(), name='traffic-api'),
]
