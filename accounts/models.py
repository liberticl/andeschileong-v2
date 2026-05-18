from datetime import datetime
from django.db import models
from django.utils import timezone
from django.db.models import Prefetch
from django.core.validators import RegexValidator
from django.contrib.auth.models import (BaseUserManager,
                                        AbstractBaseUser, PermissionsMixin)
from ciudadespendientes.models import Zone, StravaData
from django.db.models.query import QuerySet
from ciudadespendientes.choices import COUNTRIES

SEPARATORS = ['_', '-', '.']


class Permission(models.Model):
    """
        Permisos que puede tener un usuario en plataforma
    """

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"

    def __str__(self):
        return self.name


class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Account(PermissionsMixin, AbstractBaseUser):
    """
    El nombre de usuario es el correo electrónico.
    Al crearse un usuario, recibirá un mail para que active su cuenta.
    """
    email = models.EmailField(
        max_length=255, unique=True, db_index=True,
        verbose_name="Correo Electrónico")
    first_name = models.CharField(
        max_length=255, blank=True, verbose_name="Nombre(s)")
    last_name = models.CharField(
        max_length=255, blank=True, verbose_name="Apellido(s)")
    zones = models.ManyToManyField(
        Zone, blank=True, verbose_name="Zonas",
        help_text="Zonas que puede ver el usuario.")
    country = models.CharField(
        "País", max_length=20, choices=COUNTRIES, blank=True,
        help_text="País al que pertenece el usuario.")

    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_demo = models.BooleanField(default=False, verbose_name="Demo")
    is_staff = models.BooleanField(default=False,
                                   verbose_name="Andes Chile ONG")
    is_superuser = models.BooleanField(default=False,
                                       verbose_name="Superusuario")
    date_joined = models.DateTimeField(
        "Fecha de registro", default=timezone.now)
    permissions = models.ManyToManyField(
        Permission, blank=True, verbose_name="Permisos",
        help_text="Permisos que puede tener el usuario.")
    cellphone = models.CharField(
        verbose_name="Celular", max_length=56, blank=True,
        validators=[
            RegexValidator(
                r"^\+?\d{10-14}$",
                "Sólo numeros en formato internacional (+56912345678).",
                "Número inválido"
            )
        ])
    birthdate = models.DateField(
        verbose_name="Fecha de Nacimiento", blank=True, null=True,
        default=None)

    profile_picture = models.ImageField(
        upload_to="pictures", verbose_name="Foto de perfil", blank=True,
        null=True)

    # groups = models.ManyToManyField(
    #     Group, related_name="custom_account_groups", blank=True)
    # user_permissions = models.ManyToManyField(
    #     Permission, related_name="custom_account_permissions", blank=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["email"]
        verbose_name = "Cuenta de usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email

    def get_fullname(self):
        return f'{self.first_name} {self.last_name}'

    def get_shortname(self):
        if self.first_name:
            return f'{self.first_name.split()[0]}'

        email = self.email.lower()
        user_name = email.split('@')
        for sep in SEPARATORS:
            first = user_name[0]
            user_name = first.split(sep)
        return f'{user_name[0]}'

    def create_default_password(self):
        email = self.email.lower()
        user_name = email.split('@')
        for sep in SEPARATORS:
            first = user_name[0]
            user_name = first.split(sep)

        return user_name[0] + str(datetime.now().year)

    def get_user_zones(self):
        if self.is_superuser:
            qs = StravaData.objects.filter(on_mongo=True).select_related('sector')
        else:
            user_zones = self.zones.prefetch_related(
                Prefetch('sector', queryset=StravaData.objects.filter(on_mongo=True))
            ).all()
            qs = StravaData.objects.filter(on_mongo=True, sector__in=user_zones).select_related('sector')
            
        sectors_info = []
        seen = set()
        for strava in qs:
            sec = strava.sector
            if sec.id not in seen:
                sectors_info.append({
                    'id': sec.id,
                    'name': sec.name,
                    'type': sec.zone_type,
                    'country': sec.country,
                    'region_name': sec.region if hasattr(sec, 'region') and sec.region else None,
                    'available_years': sec.available_years if hasattr(sec, 'available_years') else []
                })
                seen.add(sec.id)
        return sectors_info

    def get_user_permissions(self):
        if (self.is_superuser):
            return Permission.objects.all()
        return self.permissions.all()

    def has_permission(self, permission):
        if (self.is_superuser):
            return True
        codes = [p.code for p in self.get_user_permissions()]
        return True if permission in codes else False

    def get_organizations(self):
        """
            Retorna una lista con las organizaciones en las que se
            se encuentra el usuario.
        """
        if self.is_superuser:
            return Organization.objects.filter(name='Andes Chile ONG').first()

        orgs = list(self.organization.values_list('pk', flat=True))
        return Organization.objects.filter(pk__in=orgs)

    def get_first_organization(self):
        """
            Retorna la primera organización entre las que el usuario
            se encuentra.
        """
        if isinstance(self.get_organizations(), QuerySet):
            return self.get_organizations().first()

        return self.get_organizations()

    # def send_email(self, password):
    #     """
    #         Sends welcome email
    #     """
    #     to = [self.get_full_email()]
    #     subject = 'Bienvenido a Drivetech'
    #     template_name = 'enterprises/new_user'
    #     tags = ['register', 'enterprise']
    #     context = {
    #         'password': password, 'enterprise': None,
    #         'enterprise_admin': None,
    #         'name': self.get_full_name,
    #         'email': self.email}
    #     send_email.delay(
    #         subject, to, template_name, context=context, tags=tags)


class Organization(models.Model):
    """
        Representa una organización adscrita al uso de la plataforma.
    """

    is_active = models.BooleanField(
        verbose_name='Activa', default=True,
        help_text="Indica si la organización está activa en la plataforma.")
    name = models.CharField(
        max_length=100, verbose_name="Organización")
    description = models.TextField("Descripción", blank=True, null=True)
    organization_name = models.CharField(
        u"Razón Social", max_length=255, null=True, blank=True)
    rut = models.CharField("RUT", max_length=40, null=True, blank=True)
    type = models.CharField(
        "Tipo", max_length=255, null=True, blank=True,
        help_text="Tipo de organización.")
    contact_name = models.CharField(
        "Persona de contacto", max_length=255, blank=True, null=True)
    contact_phone = models.CharField(
        "Telefono de contacto", max_length=255, blank=True, null=True)
    contact_mail = models.EmailField(
        "Email de contacto", max_length=255, blank=True, null=True)
    country = models.CharField(
        max_length=255, verbose_name='País', choices=COUNTRIES,
        default='Chile')
    big_zone = models.ForeignKey(
        Zone, verbose_name='Zona principal',
        blank=True, null=True, on_delete=models.PROTECT,
        help_text="Zona más grande a ver por alguien de esta organización.")
    region = models.CharField(
        max_length=255, verbose_name='Región', blank=True, null=True)
    comuna = models.CharField(
        max_length=255, verbose_name='Comuna', blank=True, null=True)
    address = models.CharField(
        max_length=255, verbose_name='Dirección', blank=True, null=True,
        help_text='Ej. Los Loros 66, C° La Cruz')
    coords = models.CharField(
        "Coordenadas", max_length=30,
        help_text="Ubicación en el mapa. Ej: '-33.0458456,-71.6196749'.")
    users = models.ManyToManyField(
        Account, blank=True, verbose_name='Usuarios',
        related_name='organization',
        help_text='Usuarios con acceso a la plataforma')
    website = models.CharField(
        "Pagina Web", max_length=100, blank=True, null=True)
    instagram = models.CharField(
        "Instagram", max_length=100, blank=True, null=True)
    social_media = models.CharField(
        "Otras redes sociales", max_length=255, blank=True, null=True)
    logo = models.ImageField(
        "Logo", upload_to='logos', null=True, blank=True,
        help_text='Logo de la empresa')

    class Meta:
        verbose_name = u'organización'
        verbose_name_plural = u'Organizaciones'
