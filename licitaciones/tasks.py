import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def sync_licitaciones_task(self, dias=7, ticket=None):
    """Tarea Celery: sincroniza licitaciones de Mercado Público."""
    from licitaciones.sync_engine import run_sync

    try:
        result = run_sync(dias=dias, ticket=ticket)
        logger.info(f'Sync completada: {result}')
        return result
    except Exception as exc:
        logger.error(f'Sync falló: {exc}')
        raise self.retry(exc=exc)
