from django.urls import path
from .views import intranet_dashboard, ActivityListView, ActivityCreateView, ActivityUpdateView, ActivityDeleteView

urlpatterns = [
    path('intranet/', intranet_dashboard, name='intranet_dashboard'),
    path('intranet/actividades/', ActivityListView.as_view(), name='hugo_activity_list'),
    path('intranet/actividades/add/', ActivityCreateView.as_view(), name='hugo_activity_create'),
    path('intranet/actividades/<int:pk>/edit/', ActivityUpdateView.as_view(), name='hugo_activity_update'),
    path('intranet/actividades/<int:pk>/delete/', ActivityDeleteView.as_view(), name='hugo_activity_delete'),
]
