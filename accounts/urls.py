from django.urls import path
from django.contrib.auth import views as auth_views
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

    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
         template_name='accounts/password_reset.html',
         email_template_name='email/password_reset.txt',
         html_email_template_name='email/password_reset_email.html',
         subject_template_name='email/password_reset_subject.txt',
         success_url='/accounts/password-reset/done/'),
         name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
         template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
         template_name='accounts/password_reset_confirm.html',
         success_url='/accounts/password-reset-complete/'),
         name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
         template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),

    # API
    path('api/zonas/', views.ZonesAPIView.as_view(), name='zones_api'),
    path('api/regiones/', views.RegionsAPIView.as_view(), name='regions_api'),
    path('api/comunas/', views.ComunasByRegionAPIView.as_view(), name='comunas_by_region_api'),
    path('api/organizaciones/', views.OrganizationsAPIView.as_view(), name='organizations_api'),
]
