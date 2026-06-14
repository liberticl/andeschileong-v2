import hashlib
from django.db import migrations, models


def populate_fingerprints(apps, schema_editor):
    Device = apps.get_model('mediciones', 'Device')
    for device in Device.objects.all():
        if not device.fingerprint:
            device.fingerprint = hashlib.sha256(
                (device.name or device.token or str(device.pk)).encode()
            ).hexdigest()
            device.save(update_fields=['fingerprint'])


class Migration(migrations.Migration):

    dependencies = [
        ('mediciones', '0004_trafficcount_skater_count_pet_count_device_user_agent_last_seen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='name',
            field=models.CharField(
                blank=True, default='',
                help_text="Nombre legible del dispositivo (ej: 'Providencia, RM' o 'Chrome/Linux')",
                max_length=200,
                verbose_name='Nombre'),
        ),
        migrations.AddField(
            model_name='device',
            name='fingerprint',
            field=models.CharField(
                blank=True, default='',
                help_text='Hash SHA-256 del fingerprint del navegador',
                max_length=64,
                verbose_name='Fingerprint'),
        ),
        migrations.RunPython(populate_fingerprints, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='device',
            name='fingerprint',
            field=models.CharField(
                help_text='Hash SHA-256 del fingerprint del navegador',
                max_length=64, unique=True,
                verbose_name='Fingerprint'),
        ),
    ]
