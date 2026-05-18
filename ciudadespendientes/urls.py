from django.urls import path
from . import views

urlpatterns = [
    path('', views.find, name='buscar'),
    path('mapa/', views.show_data, name='show_data'),
]
