from . import models
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import AccountChangeForm, AccountCreationForm


@admin.register(models.Account)
class AccountAdmin(UserAdmin):
    # The forms to add and change user instances
    form = AccountChangeForm
    add_form = AccountCreationForm

    list_display = (
        'email', '_get_fullname', '_get_organizations', 'cellphone',
        'country', 'is_active', 'last_login')
    list_filter = (
        'is_active', 'country', 'zones', 'permissions',)
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'email', 'first_name', 'last_name', 'cellphone',
                'birthdate', 'country', 'password',)}),
        ('Sobre el usuario', {
            'fields': ('is_active', 'is_demo', 'is_staff', 'is_superuser',)}),
        ('Accesos', {
            'fields': ('zones', 'permissions',)}),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined',)}),
        # ('Ajustes', {'fields': ('timezone', 'settings',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',)}  # 'password1', 'password2')}
         ),
    )
    search_fields = (
        'email', 'first_name', 'last_name',)
    ordering = ('email',)
    filter_horizontal = ('zones', 'permissions')

    def _get_fullname(self, obj):
        """
            Entrega el nombre completo del usuario
        """
        return obj.get_fullname()

    def _get_organizations(self, obj):
        """
            Entrega las organizaciones del usuario
        """
        if (obj.is_superuser):
            return 'Andes Chile ONG'
        return ', '.join([o.name for o in obj.get_organizations()])

    _get_fullname.short_description = 'Nombre Completo'
    _get_organizations.short_description = 'Organizaciones'

    # actions = [
    #     actions.set_password,
    #     actions.reset_pin,
    #     actions.send_email,
    #     actions.generate_permissions_token,
    #     actions.generate_vehicles_token,
    #     actions.delete_user_sessions,
    #     actions.clean_user
    # ]
    # inlines = (EnterprisePermissionInline, NotificationInline,)


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
        Sitio administrativo para Organization
    """
    list_display = ('name', 'is_active', 'type', 'contact_name',
                    'contact_phone', 'country', 'big_zone',)
    list_filter = ('name', 'is_active', 'type', 'country',
                   'big_zone',)
    search_fields = ('name', 'organization_name', 'rut', 'contact_name',
                     'contact_phone', 'contact_mail', 'type',)
    fieldsets = (
        ('General', {
            'fields': (
                'is_active', 'name', 'description', 'type', 'country',
                'big_zone', 'coords')}),
        ('Información de Contacto', {
            'fields': (
                'contact_name', 'contact_mail', 'contact_phone',)}),
        ('Información Oficial', {
            'fields': ('organization_name', 'rut', 'address', 'comuna',
                       'region',)}),
        ('Otros', {
            'fields': (
                'users', 'website', 'instagram', 'social_media', 'logo',)})
    )
    filter_horizontal = ('users',)


@admin.register(models.Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code',)
    list_filter = ('name', 'code',)
