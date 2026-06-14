from django.db import models
from django.db.models.signals import pre_save
from andeschileong.settings import CP_JWT_SECRET
import jwt


class Device(models.Model):
    """
    Modelo para gestionar dispositivos, su ubicación y tokens únicos.
    """
    name = models.CharField(
        "Nombre", max_length=100, unique=True,
        help_text="Nombre único para el dispositivo")
    is_active = models.BooleanField(
        "Activo", default=True,
        help_text="Indica si el dispositvo está activo.")
    token = models.CharField(
        "Token", max_length=256, unique=True,
        help_text="Token de autenticación único para el dispositivo")
    coords = models.CharField(
        "Coordenadas", max_length=30,
        help_text="Ubicación del dispositivo. Ej: '-33.0458456,-71.6196749'.")

    class Meta:
        verbose_name_plural = "Dispositivos"

    def __str__(self):
        return self.name

    @classmethod
    def before_save(cls, sender, instance, **kwargs):
        if not instance.token:
            instance.token = jwt.encode(
                {'devicename': instance.name,
                 'devicecoords': instance.coords},
                CP_JWT_SECRET,
                algorithm='HS256'
                )


pre_save.connect(Device.before_save, sender=Device)


class TrafficCount(models.Model):
    """
    Modelo para almacenar datos agrupados de tráfico.
    """
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, verbose_name="Dispositivo")
    datetime = models.DateTimeField(
        "Hora y fecha de medición", help_text="Fecha y hora de la medición")
    created_datetime = models.DateTimeField(
        "Hora y fecha de creación", help_text="Fecha y hora de creación")
    car_count = models.PositiveIntegerField(
        "Cantidad de autos", default=0)
    person_count = models.PositiveIntegerField(
        "Cantidad de peatones", default=0)
    bicycle_count = models.PositiveIntegerField(
        "Cantidad de bicicletas", default=0)
    motorcycle_count = models.PositiveIntegerField(
        "Cantidad de motos", default=0)
    truck_count = models.PositiveIntegerField(
        "Cantidad de camiones", default=0)
    bus_count = models.PositiveIntegerField(
        "Cantidad de buses", default=0)

    class Meta:
        verbose_name_plural = "Conteo de tráfico"
        ordering = ['-datetime']

    def __str__(self):
        return f"Registro de {self.device.name} a las {self.datetime}" # noqa
