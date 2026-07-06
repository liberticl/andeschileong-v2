from django.core.management.base import BaseCommand
from accounts.utils import send_email


class Command(BaseCommand):
    help = 'Envía un correo de prueba a francisco@andeschileong.cl'

    def handle(self, *args, **options):
        self.stdout.write('Enviando correo de prueba...')

        result = send_email(
            subject='Correo de prueba — Andes Chile ONG',
            template_name='email/generic.html',
            context={
                'subject': 'Correo de prueba',
                'message': 'Este es un correo de prueba enviado desde el sistema Django de Andes Chile ONG.\n\nSi recibiste este mensaje, la configuración SMTP está funcionando correctamente.',
            },
            recipients='francisco@andeschileong.cl',
        )

        if result:
            self.stdout.write(self.style.SUCCESS('Correo enviado exitosamente.'))
        else:
            self.stdout.write(self.style.ERROR('Error al enviar el correo.'))
