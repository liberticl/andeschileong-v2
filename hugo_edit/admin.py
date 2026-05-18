from django.contrib import admin
from .models import Activity

class HugoAdminSite(admin.AdminSite):
    site_header = 'Hugo Site Editor'
    site_title = 'Hugo Editor'
    index_title = 'Administración de Contenido Hugo'

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser

hugo_admin_site = HugoAdminSite(name='hugo_admin')

class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'date')
    search_fields = ('title', 'tags')

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css',)
        }
        js = (
            'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js',
            'hugo_edit/js/simplemde_init.js',
        )

hugo_admin_site.register(Activity, ActivityAdmin)

# Si el usuario quiere verlo también en su admin general django
admin.site.register(Activity, ActivityAdmin)
