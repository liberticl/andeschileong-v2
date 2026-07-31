import uuid
from django.db import models
from django.conf import settings


class SenderAccount(models.Model):
    email = models.EmailField(
        unique=True, verbose_name="Correo del remitente",
        help_text="Cuenta Gmail para envío (ej: noreply@andeschileong.cl)")
    display_name = models.CharField(
        max_length=100, verbose_name="Nombre visible",
        help_text="Nombre que aparece como remitente")
    daily_limit = models.IntegerField(
        default=10000, verbose_name="Límite diario",
        help_text="Máximo de correos por día (10000 para smtp-relay)")
    is_active = models.BooleanField(
        default=True, verbose_name="Activa",
        help_text="Si está habilitada para envío")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuenta remitente"
        verbose_name_plural = "Cuentas remitentes"
        ordering = ['-is_active', 'email']

    def __str__(self):
        return f"{self.display_name} <{self.email}>"

    def sent_today(self):
        from django.utils import timezone
        today = timezone.now().date()
        return EmailLog.objects.filter(
            sender_account=self,
            status='sent',
            sent_at__date=today
        ).count()

    def remaining_today(self):
        return max(0, self.daily_limit - self.sent_today())


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
    ]

    batch_id = models.UUIDField(
        default=uuid.uuid4, db_index=True, verbose_name="ID de lote")
    batch_label = models.CharField(
        max_length=200, blank=True, verbose_name="Etiqueta del lote",
        help_text="Nombre descriptivo (ej: Boletín julio 2026)")
    recipient_email = models.EmailField(
        db_index=True, verbose_name="Correo destinatario")
    recipient_name = models.CharField(
        max_length=200, blank=True, verbose_name="Nombre destinatario")
    subject = models.CharField(
        max_length=500, verbose_name="Asunto")
    template_name = models.CharField(
        max_length=100, verbose_name="Template utilizado")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        db_index=True, verbose_name="Estado")
    sender_account = models.ForeignKey(
        SenderAccount, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Cuenta remitente")
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name="Enviado por")
    sent_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de envío")
    error_message = models.TextField(
        blank=True, verbose_name="Mensaje de error")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de correo"
        verbose_name_plural = "Logs de correos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['batch_id', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.recipient_email} - {self.get_status_display()}"
