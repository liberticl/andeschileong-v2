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
    list_display = ('device', 'datetime', 'created_datetime',
                    'direction_summary', 'line_summary')
    list_filter = ('device',)
    search_fields = ('device',)
    fieldsets = (
        ('General', {
            'fields': (
                'device', 'datetime', 'created_datetime')}),
        ('Conteo (totales)', {
            'fields': (
                'car_count', 'person_count', 'bicycle_count',
                'motorcycle_count', 'truck_count', 'bus_count',
                'skater_count', 'pet_count',)}),
        ('Línea y lados (referencia: A=start, B=end)', {
            'fields': (
                'line_x1', 'line_y1', 'line_x2', 'line_y2',
                'side_a_name', 'side_b_name',)}),
        ('Dirección A→B', {
            'fields': (
                'car_a_to_b', 'person_a_to_b', 'bicycle_a_to_b',
                'motorcycle_a_to_b', 'truck_a_to_b', 'bus_a_to_b',
                'skater_a_to_b', 'pet_a_to_b',)}),
        ('Dirección B→A', {
            'fields': (
                'car_b_to_a', 'person_b_to_a', 'bicycle_b_to_a',
                'motorcycle_b_to_a', 'truck_b_to_a', 'bus_b_to_a',
                'skater_b_to_a', 'pet_b_to_a',)}),
    )

    def direction_summary(self, obj):
        if not obj.has_direction_data:
            return 'sin dirección'
        parts = []
        for field in obj.COUNT_FIELDS:
            base = field[:-len('_count')]
            a = getattr(obj, f"{base}_a_to_b", 0) or 0
            b = getattr(obj, f"{base}_b_to_a", 0) or 0
            if a or b:
                parts.append(f"{base}:{a}→/{b}←")
        return ' '.join(parts)
    direction_summary.short_description = 'A→B / B→A'

    def line_summary(self, obj):
        line = obj.get_line_dict()
        a = (obj.side_a_name or '').strip()
        b = (obj.side_b_name or '').strip()
        tag = f'A({a})→B({b})' if (a or b) else 'A→B'
        if not line:
            return f'{tag} sin línea'
        return f"{tag} ({line['x1']:.2f},{line['y1']:.2f})→({line['x2']:.2f},{line['y2']:.2f})"
    line_summary.short_description = 'Línea'
