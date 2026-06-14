from django.contrib import admin
from . import models


@admin.register(models.Device)
class DeviceAdmin(admin.ModelAdmin):
    """
        Sitio administrativo para Device
    """
    list_display = ('name', 'fingerprint_short', 'is_active', 'last_seen', 'token')
    list_filter = ('is_active',)
    search_fields = ('name', 'fingerprint', 'token', 'coords')
    readonly_fields = ('token', 'fingerprint')
    fieldsets = (
        ('General', {
            'fields': (
                'is_active', 'name', 'fingerprint', 'token', 'coords',
                'user_agent', 'last_seen',)}),
    )

    def fingerprint_short(self, obj):
        return obj.fingerprint[:12] + '...' if obj.fingerprint else ''
    fingerprint_short.short_description = 'Fingerprint'


@admin.register(models.TrafficCount)
class TrafficCountAdmin(admin.ModelAdmin):
    """
        Sitio administrativo para TrafficCount
    """
    list_display = ('device', 'datetime', 'created_datetime')
    list_filter = ('device',)
    search_fields = ('device',)
    fieldsets = (
        ('General', {
            'fields': (
                'device', 'datetime', 'created_datetime')}),
        ('Conteo', {
            'fields': (
                'car_count', 'person_count', 'bicycle_count',
                'motorcycle_count', 'truck_count', 'bus_count',
                'skater_count', 'pet_count',)}),
    )
