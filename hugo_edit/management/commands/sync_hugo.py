from django.core.management.base import BaseCommand
from hugo_edit.models import Activity, Noticia, Estudio
import subprocess
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Sincroniza la Base de Datos con los ficheros Markdown de Hugo'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generando ficheros Markdown desde la Base de Datos...')

        for act in Activity.objects.all():
            act.generate_markdown()
            self.stdout.write(f'- Actividad: {act.title}')

        for noticia in Noticia.objects.all():
            noticia.generate_markdown()
            self.stdout.write(f'- Noticia: {noticia.title}')

        for estudio in Estudio.objects.all():
            estudio.generate_markdown()
            self.stdout.write(f'- Estudio: {estudio.title}')

        self.stdout.write('Reconstruyendo Hugo site...')
        result = subprocess.run(
            ['hugo', '--minify'],
            cwd=os.path.join(settings.BASE_DIR, 'hugo_site'),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            self.stdout.write(self.style.SUCCESS('Sincronización de Hugo completada exitosamente.'))
        else:
            self.stdout.write(self.style.ERROR(f'Error al compilar Hugo: {result.stderr}'))
