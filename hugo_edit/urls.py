from django.urls import path
from .views import (
    intranet_dashboard,
    restore_activity, restore_noticia, restore_estudio,
    ActivityListView, ActivityCreateView, ActivityUpdateView, ActivityDeleteView,
    NoticiaListView, NoticiaCreateView, NoticiaUpdateView, NoticiaDeleteView,
    EstudioListView, EstudioCreateView, EstudioUpdateView, EstudioDeleteView,
    ActivityDeletedView, NoticiaDeletedView, EstudioDeletedView,
    RegistrationRequestListView, RegistrationRequestDetailView,
    RegistrationRequestApproveView, RegistrationRequestRejectView,
)

urlpatterns = [
    path('intranet/', intranet_dashboard, name='intranet_dashboard'),

    path('intranet/actividades/', ActivityListView.as_view(), name='hugo_activity_list'),
    path('intranet/actividades/add/', ActivityCreateView.as_view(), name='hugo_activity_create'),
    path('intranet/actividades/<int:pk>/edit/', ActivityUpdateView.as_view(), name='hugo_activity_update'),
    path('intranet/actividades/<int:pk>/delete/', ActivityDeleteView.as_view(), name='hugo_activity_delete'),
    path('intranet/actividades/<int:pk>/restore/', restore_activity, name='hugo_activity_restore'),
    path('intranet/actividades/eliminados/', ActivityDeletedView.as_view(), name='hugo_activity_deleted'),

    path('intranet/noticias/', NoticiaListView.as_view(), name='hugo_noticia_list'),
    path('intranet/noticias/add/', NoticiaCreateView.as_view(), name='hugo_noticia_create'),
    path('intranet/noticias/<int:pk>/edit/', NoticiaUpdateView.as_view(), name='hugo_noticia_update'),
    path('intranet/noticias/<int:pk>/delete/', NoticiaDeleteView.as_view(), name='hugo_noticia_delete'),
    path('intranet/noticias/<int:pk>/restore/', restore_noticia, name='hugo_noticia_restore'),
    path('intranet/noticias/eliminados/', NoticiaDeletedView.as_view(), name='hugo_noticia_deleted'),

    path('intranet/estudios/', EstudioListView.as_view(), name='hugo_estudio_list'),
    path('intranet/estudios/add/', EstudioCreateView.as_view(), name='hugo_estudio_create'),
    path('intranet/estudios/<int:pk>/edit/', EstudioUpdateView.as_view(), name='hugo_estudio_update'),
    path('intranet/estudios/<int:pk>/delete/', EstudioDeleteView.as_view(), name='hugo_estudio_delete'),
    path('intranet/estudios/<int:pk>/restore/', restore_estudio, name='hugo_estudio_restore'),
    path('intranet/estudios/eliminados/', EstudioDeletedView.as_view(), name='hugo_estudio_deleted'),

    path('intranet/solicitudes/', RegistrationRequestListView.as_view(), name='hugo_registration_request_list'),
    path('intranet/solicitudes/<int:pk>/', RegistrationRequestDetailView.as_view(), name='hugo_registration_request_detail'),
    path('intranet/solicitudes/<int:pk>/aprobar/', RegistrationRequestApproveView.as_view(), name='hugo_registration_request_approve'),
    path('intranet/solicitudes/<int:pk>/rechazar/', RegistrationRequestRejectView.as_view(), name='hugo_registration_request_reject'),
]
