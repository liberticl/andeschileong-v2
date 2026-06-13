from django.contrib import admin
from .models import Licitacion, SyncLog


@admin.register(Licitacion)
class LicitacionAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'nombre_corto', 'organismo', 'estado',
        'monto_display', 'region', 'fecha_publicacion')
    list_filter = ('estado', 'region', 'tipo_licitacion')
    search_fields = ('codigo', 'nombre', 'organismo')
    readonly_fields = ('raw_data', 'fecha_sync', 'palabras_clave')
    list_per_page = 25

    fieldsets = (
        ('Identificación', {
            'fields': ('codigo', 'nombre', 'tipo_licitacion', 'estado')}),
        ('Organismo', {
            'fields': ('organismo', 'codigo_organismo')}),
        ('Montos y Fechas', {
            'fields': ('monto_estimado', 'moneda',
                       'fecha_publicacion', 'fecha_cierre')}),
        ('Ubicación', {
            'fields': ('comuna', 'region')}),
        ('Metadata', {
            'fields': ('palabras_clave', 'raw_data', 'fecha_sync', 'activo')}),
    )

    actions = ['activar', 'desactivar']

    def nombre_corto(self, obj):
        return obj.nombre[:80] + '...' if len(obj.nombre) > 80 else obj.nombre
    nombre_corto.short_description = 'Nombre'

    def monto_display(self, obj):
        return obj.get_monto_display()
    monto_display.short_description = 'Monto'

    @admin.action(description='Activar seleccionadas')
    def activar(self, request, queryset):
        count = queryset.update(activo=True)
        self.message_user(request, f"{count} licitaciones activadas.")

    @admin.action(description='Desactivar seleccionadas')
    def desactivar(self, request, queryset):
        count = queryset.update(activo=False)
        self.message_user(request, f"{count} licitaciones desactivadas.")


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 'licitaciones_consultadas', 'licitaciones_filtradas',
        'licitaciones_nuevas', 'licitaciones_actualizadas',
        'errores', 'duracion_display', 'exitoso')
    list_filter = ('exitoso',)
    readonly_fields = (
        'fecha', 'licitaciones_consultadas', 'licitaciones_filtradas',
        'licitaciones_nuevas', 'licitaciones_actualizadas',
        'errores', 'duracion_segundos', 'exitoso', 'detalle')
    list_per_page = 20

    def has_add_permission(self, request):
        return False

    def duracion_display(self, obj):
        return f"{obj.duracion_segundos:.1f}s"
    duracion_display.short_description = 'Duración'
