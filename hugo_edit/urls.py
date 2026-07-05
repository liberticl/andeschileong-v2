from django.urls import path
from .views import (
    intranet_dashboard,
    ActivityListView, ActivityCreateView, ActivityUpdateView, ActivityDeleteView,
    NoticiaListView, NoticiaCreateView, NoticiaUpdateView, NoticiaDeleteView,
    EstudioListView, EstudioCreateView, EstudioUpdateView, EstudioDeleteView,
)

urlpatterns = [
    path('intranet/', intranet_dashboard, name='intranet_dashboard'),

    path('intranet/actividades/', ActivityListView.as_view(), name='hugo_activity_list'),
    path('intranet/actividades/add/', ActivityCreateView.as_view(), name='hugo_activity_create'),
    path('intranet/actividades/<int:pk>/edit/', ActivityUpdateView.as_view(), name='hugo_activity_update'),
    path('intranet/actividades/<int:pk>/delete/', ActivityDeleteView.as_view(), name='hugo_activity_delete'),

    path('intranet/noticias/', NoticiaListView.as_view(), name='hugo_noticia_list'),
    path('intranet/noticias/add/', NoticiaCreateView.as_view(), name='hugo_noticia_create'),
    path('intranet/noticias/<int:pk>/edit/', NoticiaUpdateView.as_view(), name='hugo_noticia_update'),
    path('intranet/noticias/<int:pk>/delete/', NoticiaDeleteView.as_view(), name='hugo_noticia_delete'),

    path('intranet/estudios/', EstudioListView.as_view(), name='hugo_estudio_list'),
    path('intranet/estudios/add/', EstudioCreateView.as_view(), name='hugo_estudio_create'),
    path('intranet/estudios/<int:pk>/edit/', EstudioUpdateView.as_view(), name='hugo_estudio_update'),
    path('intranet/estudios/<int:pk>/delete/', EstudioDeleteView.as_view(), name='hugo_estudio_delete'),
]
