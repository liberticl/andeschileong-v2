from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('lista/', views.licitaciones_list, name='licitaciones_list'),
    path('<str:codigo>/', views.licitacion_detalle, name='detalle'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('sync/', views.trigger_sync, name='trigger_sync'),
]
