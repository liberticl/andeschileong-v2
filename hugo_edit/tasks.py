import logging
import os
import subprocess

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def rebuild_hugo():
    """Tarea Celery: reconstruye el sitio Hugo."""
    try:
        result = subprocess.run(
            ['hugo', '--minify'],
            cwd=os.path.join(settings.BASE_DIR, 'hugo_site'),
            timeout=60,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f'Hugo rebuild falló: {result.stderr}')
        else:
            logger.info('Hugo rebuild completado exitosamente')
        return result.returncode
    except subprocess.TimeoutExpired:
        logger.error('Hugo rebuild excedió el timeout de 60s')
        raise
    except Exception as exc:
        logger.error(f'Hugo rebuild falló con excepción: {exc}')
        raise
