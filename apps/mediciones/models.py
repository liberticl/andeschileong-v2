from django.db import models
from django.db.models.signals import pre_save
from django.utils import timezone
from andeschileong.settings import CP_JWT_SECRET
import jwt


class Device(models.Model):
    """
    Modelo para gestionar dispositivos, su ubicación y tokens únicos.
    """
    name = models.CharField(
        "Nombre", max_length=200, blank=True, default='',
        help_text="Nombre legible del dispositivo (ej: 'Providencia, RM' o 'Chrome/Linux')")
    fingerprint = models.CharField(
        "Fingerprint", max_length=64, unique=True,
        help_text="Hash SHA-256 del fingerprint del navegador")
    is_active = models.BooleanField(
        "Activo", default=True,
        help_text="Indica si el dispositvo está activo.")
    token = models.CharField(
        "Token", max_length=512, unique=True,
        help_text="Token de autenticación único para el dispositivo")
    coords = models.CharField(
        "Coordenadas", max_length=30, blank=True, default='',
        help_text="Ubicación del dispositivo. Ej: '-33.0458456,-71.6196749'.")
    user_agent = models.CharField(
        "User Agent", max_length=500, blank=True, default='',
        help_text="Navegador y SO del dispositivo.")
    last_seen = models.DateTimeField(
        "Última conexión", null=True, blank=True,
        help_text="Fecha y hora de la última conexión del dispositivo.")

    class Meta:
        verbose_name_plural = "Dispositivos"

    def __str__(self):
        return self.name or self.fingerprint[:16]

    @classmethod
    def before_save(cls, sender, instance, **kwargs):
        if not instance.token:
            instance.token = jwt.encode(
                {'devicename': instance.name or instance.fingerprint,
                 'devicecoords': instance.coords,
                 'fingerprint': instance.fingerprint},
                CP_JWT_SECRET,
                algorithm='HS256'
                )


pre_save.connect(Device.before_save, sender=Device)


class TrafficCount(models.Model):
    """
    Modelo para almacenar datos agrupados de tráfico.

    Convención de dirección A/B (ver docs/api.md §3 y docs/guia-dispositivos.md §7):
    la línea de conteo se define por dos puntos normalizados 0-1
    (``line_x1,line_y1`` = punto A = start, ``line_x2,line_y2`` = punto B = end).
    Para cada detección se usa el footPoint (centro-inferior del bbox) y
    ``signedDistance = (end-start) x (point-start)`` (producto cruzado 2D):
    ``< -12px`` = lado A (-1), ``> +12px`` = lado B (+1), en medio = deadzone.
    ``A->B`` = cruce -1 → +1, ``B->A`` = cruce +1 → -1.
    Los campos ``*_count`` son siempre el total; ``*_a_to_b`` / ``*_b_to_a``
    son el desglose opcional (0 = sin dato direccional). Si ``line_*`` es NULL
    el registro es conteo por aparición (sin línea, sin dirección).
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
    skater_count = models.PositiveIntegerField(
        "Cantidad de patinantes", default=0)
    pet_count = models.PositiveIntegerField(
        "Cantidad de mascotas", default=0)

    # Línea de conteo normalizada 0-1 (A=start, B=end). NULL = sin línea.
    line_x1 = models.FloatField(
        "Línea A.x (0-1)", null=True, blank=True,
        help_text="Extremo A (start) de la línea, coordenada x normalizada 0-1.")
    line_y1 = models.FloatField(
        "Línea A.y (0-1)", null=True, blank=True,
        help_text="Extremo A (start) de la línea, coordenada y normalizada 0-1.")
    line_x2 = models.FloatField(
        "Línea B.x (0-1)", null=True, blank=True,
        help_text="Extremo B (end) de la línea, coordenada x normalizada 0-1.")
    line_y2 = models.FloatField(
        "Línea B.y (0-1)", null=True, blank=True,
        help_text="Extremo B (end) de la línea, coordenada y normalizada 0-1.")

    # Nombres de referencia de cada lado (editables en el front, por captura).
    side_a_name = models.CharField(
        "Nombre lado A", max_length=100, blank=True, default='',
        help_text="Referencia del lado A (-1), ej: 'Norte'.")
    side_b_name = models.CharField(
        "Nombre lado B", max_length=100, blank=True, default='',
        help_text="Referencia del lado B (+1), ej: 'Sur'.")

    # Desglose direccional opcional (0 = sin dato). total == a_to_b + b_to_a.
    car_a_to_b = models.PositiveIntegerField("Autos A→B", default=0)
    car_b_to_a = models.PositiveIntegerField("Autos B→A", default=0)
    person_a_to_b = models.PositiveIntegerField("Peatones A→B", default=0)
    person_b_to_a = models.PositiveIntegerField("Peatones B→A", default=0)
    bicycle_a_to_b = models.PositiveIntegerField("Bicicletas A→B", default=0)
    bicycle_b_to_a = models.PositiveIntegerField("Bicicletas B→A", default=0)
    motorcycle_a_to_b = models.PositiveIntegerField("Motos A→B", default=0)
    motorcycle_b_to_a = models.PositiveIntegerField("Motos B→A", default=0)
    truck_a_to_b = models.PositiveIntegerField("Camiones A→B", default=0)
    truck_b_to_a = models.PositiveIntegerField("Camiones B→A", default=0)
    bus_a_to_b = models.PositiveIntegerField("Buses A→B", default=0)
    bus_b_to_a = models.PositiveIntegerField("Buses B→A", default=0)
    skater_a_to_b = models.PositiveIntegerField("Patinantes A→B", default=0)
    skater_b_to_a = models.PositiveIntegerField("Patinantes B→A", default=0)
    pet_a_to_b = models.PositiveIntegerField("Mascotas A→B", default=0)
    pet_b_to_a = models.PositiveIntegerField("Mascotas B→A", default=0)

    COUNT_FIELDS = (
        'car_count', 'person_count', 'bicycle_count',
        'motorcycle_count', 'truck_count', 'bus_count',
        'skater_count', 'pet_count',
    )
    LINE_FIELDS = ('line_x1', 'line_y1', 'line_x2', 'line_y2')

    class Meta:
        verbose_name_plural = "Conteo de tráfico"
        ordering = ['-datetime']

    def __str__(self):
        return f"Registro de {self.device.name} a las {self.datetime}" # noqa

    @property
    def has_line(self):
        """True si la línea A/B está completa (4 coords no nulas)."""
        return all(getattr(self, f) is not None for f in self.LINE_FIELDS)

    @property
    def has_direction_data(self):
        """True si hay al menos un cruce direccional registrado."""
        for field in self.COUNT_FIELDS:
            base = field[:-len('_count')]
            if getattr(self, f"{base}_a_to_b", 0) or getattr(self, f"{base}_b_to_a", 0):
                return True
        return False

    def get_line_dict(self):
        """Línea como dict normalizado o None (sin línea)."""
        if not self.has_line:
            return None
        return {'x1': self.line_x1, 'y1': self.line_y1,
                'x2': self.line_x2, 'y2': self.line_y2}

    def get_direction_counts_dict(self):
        """Desglose ``{a_to_b: {...}, b_to_a: {...}}`` con claves ``*_count``."""
        a_to_b, b_to_a = {}, {}
        for field in self.COUNT_FIELDS:
            base = field[:-len('_count')]
            a_to_b[field] = getattr(self, f"{base}_a_to_b", 0) or 0
            b_to_a[field] = getattr(self, f"{base}_b_to_a", 0) or 0
        return {'a_to_b': a_to_b, 'b_to_a': b_to_a}
