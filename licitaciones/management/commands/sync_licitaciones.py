from django.core.management.base import BaseCommand
import os

from licitaciones.sync_engine import run_sync


class Command(BaseCommand):
    help = 'Sincroniza licitaciones de Mercado Público'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias', type=int, default=7,
            help='Días hacia atrás para buscar')
        parser.add_argument(
            '--ticket', type=str, default=None,
            help='Ticket de API (default: MERCADO_PUBLICO_TICKET env)')

    def handle(self, *args, **options):
        ticket = options['ticket'] or os.environ.get('MERCADO_PUBLICO_TICKET')
        if not ticket:
            self.stdout.write(self.style.ERROR(
                'No se encontró ticket. '
                'Usa --ticket o configura MERCADO_PUBLICO_TICKET en .env'))
            return

        result = run_sync(dias=options['dias'], ticket=ticket)

        self.stdout.write(self.style.SUCCESS(
            f'Sync completada: {result["nuevas"]} nuevas, '
            f'{result["actualizadas"]} actualizadas, '
            f'{result["filtradas"]} filtradas de '
            f'{result["consultadas"]} consultadas, '
            f'{result["detalles_ok"]} detalles OK '
            f'({result["duracion"]:.1f}s)'))
