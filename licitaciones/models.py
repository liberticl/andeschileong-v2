from django.db import models


class Licitacion(models.Model):
    """
    Licitaciones de infraestructura ciclista/peatonal
    obtenidas de Mercado Público.
    """
    ESTADOS = [
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
        ('desierta', 'Desierta'),
        ('adjudicada', 'Adjudicada'),
        ('revocada', 'Revocada'),
        ('suspendida', 'Suspendida'),
    ]

    TIPOS = {
        'L1': 'Pública < 100 UTM',
        'LE': 'Pública 100-1000 UTM',
        'LP': 'Pública 1000+ UTM',
        'LQ': 'Pública 2000-5000 UTM',
        'LR': 'Pública ≥ 5000 UTM',
        'LS': 'Servicios personales',
        'E2': 'Privada < 100 UTM',
        'CO': 'Privada 100-1000 UTM',
        'B2': 'Privada 1000-2000 UTM',
        'H2': 'Privada 2000-5000 UTM',
        'I2': 'Privada > 5000 UTM',
        'O1': 'Obra pública',
    }

    codigo = models.CharField("Código licitación", max_length=50, unique=True)
    nombre = models.CharField("Nombre", max_length=500)
    organismo = models.CharField("Organismo comprador", max_length=300)
    codigo_organismo = models.IntegerField("Código organismo", null=True)
    monto_estimado = models.DecimalField(
        "Monto estimado", max_digits=15, decimal_places=2, null=True)
    moneda = models.CharField("Moneda", max_length=5, default='CLP')
    estado = models.CharField("Estado", max_length=20, choices=ESTADOS)
    fecha_cierre = models.DateTimeField("Fecha cierre", null=True, blank=True)
    fecha_publicacion = models.DateTimeField(
        "Fecha publicación", null=True, blank=True)
    tipo_licitacion = models.CharField("Tipo licitación", max_length=5)

    comuna = models.CharField("Comuna", max_length=100, blank=True)
    region = models.CharField("Región", max_length=100, blank=True)

    palabras_clave = models.JSONField(
        "Palabras clave encontradas", default=list)
    raw_data = models.JSONField("Datos originales API", default=dict)
    fecha_sync = models.DateTimeField("Última sincronización", auto_now=True)
    activo = models.BooleanField("Activo", default=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre[:60]}"

    def get_monto_display(self):
        if self.monto_estimado is None:
            return '-'
        if self.monto_estimado >= 1_000_000_000:
            return f"${self.monto_estimado / 1_000_000_000:.1f}B {self.moneda}"
        if self.monto_estimado >= 1_000_000:
            return f"${self.monto_estimado / 1_000_000:.0f}M {self.moneda}"
        return f"${self.monto_estimado:,.0f} {self.moneda}"

    def get_tipo_display(self):
        return self.TIPOS.get(self.tipo_licitacion, self.tipo_licitacion)

    class Meta:
        verbose_name = "licitación"
        verbose_name_plural = "Licitaciones"
        ordering = ['-fecha_publicacion']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['region']),
            models.Index(fields=['-fecha_publicacion']),
        ]


class SyncLog(models.Model):
    """
    Registro de sincronizaciones con Mercado Público.
    """
    fecha = models.DateTimeField(auto_now_add=True)
    licitaciones_consultadas = models.IntegerField(default=0)
    licitaciones_filtradas = models.IntegerField(default=0)
    licitaciones_nuevas = models.IntegerField(default=0)
    licitaciones_actualizadas = models.IntegerField(default=0)
    errores = models.IntegerField(default=0)
    duracion_segundos = models.FloatField(default=0)
    exitoso = models.BooleanField(default=True)
    detalle = models.TextField(blank=True)

    def __str__(self):
        return (
            f"Sync {self.fecha.strftime('%Y-%m-%d %H:%M')} "
            f"- {self.licitaciones_nuevas} nuevas"
        )

    class Meta:
        verbose_name = "log de sincronización"
        verbose_name_plural = "Logs de sincronización"
        ordering = ['-fecha']
