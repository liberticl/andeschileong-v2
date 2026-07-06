from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.RegistrationRequestCreateView.as_view(),
         name='registration_request'),
    path('solicitud-exitosa/', views.RegistrationRequestSuccessView.as_view(),
         name='registration_request_success'),
    path('activar/<uuid:token>/', views.ActivateAccountView.as_view(),
         name='activate_account'),
    path('activacion-completa/', views.ActivationCompleteView.as_view(),
         name='activation_complete'),
    path('api/zonas/', views.ZonesAPIView.as_view(), name='zones_api'),
    path('api/regiones/', views.RegionsAPIView.as_view(), name='regions_api'),
    path('api/comunas/', views.ComunasByRegionAPIView.as_view(), name='comunas_by_region_api'),
    path('api/organizaciones/', views.OrganizationsAPIView.as_view(), name='organizations_api'),
]
