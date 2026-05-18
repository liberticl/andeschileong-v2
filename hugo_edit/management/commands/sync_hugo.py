from django.core.management.base import BaseCommand
from hugo_edit.models import Activity
import subprocess
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Sincroniza la Base de Datos con los ficheros Markdown de Hugo'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generando ficheros Markdown desde la Base de Datos...')
        activities = Activity.objects.all()
        
        for act in activities:
            act.generate_markdown()
            self.stdout.write(f'- Creado: {act.title}')
            
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
