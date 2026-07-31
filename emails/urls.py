from django.urls import path
from . import views

urlpatterns = [
    path('intranet/correos/', views.email_logs, name='email_logs'),
    path('intranet/correos/nuevo/', views.compose_email, name='email_compose'),
    path('intranet/correos/cuentas/',
         views.sender_accounts, name='email_sender_accounts'),
    path('intranet/correos/<uuid:batch_id>/',
         views.email_log_detail, name='email_log_detail'),
    path('intranet/correos/<uuid:batch_id>/reintentar/',
         views.email_retry_failed, name='email_retry_failed'),
]
