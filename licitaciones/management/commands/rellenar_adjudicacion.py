from django.core.management.base import BaseCommand

from licitaciones.models import Licitacion
from licitaciones.sync_engine import _calc_adjudicacion


class Command(BaseCommand):
    help = 'Backfill monto adjudicado/proveedor/oferentes/acta/reclamos desde raw_data (sin API)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--codigo', type=str, default=None,
            help='Solo un código específico')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='No guarda, solo muestra lo que haría')

    def handle(self, *args, **options):
        qs = Licitacion.objects.filter(activo=True)
        if options['codigo']:
            qs = qs.filter(codigo=options['codigo'])
        total = qs.count()
        upd = 0
        for lic in qs.iterator():
            adj = _calc_adjudicacion(lic.raw_data or {})
            changed = (
                lic.monto_adjudicado != adj['monto_adjudicado']
                or (lic.proveedor_adjudicado or '') != adj['proveedor_adjudicado']
                or lic.n_oferentes != adj['n_oferentes']
                or (lic.url_acta or '') != adj['url_acta']
                or lic.n_reclamos != adj['n_reclamos']
            )
            if not changed:
                continue
            if options['dry_run']:
                self.stdout.write(
                    f'  {lic.codigo}: adj={adj["monto_adjudicado"]} '
                    f'prov={adj["proveedor_adjudicado"][:40]}')
                continue
            lic.monto_adjudicado = adj['monto_adjudicado']
            lic.proveedor_adjudicado = adj['proveedor_adjudicado']
            lic.n_oferentes = adj['n_oferentes']
            lic.url_acta = adj['url_acta']
            lic.n_reclamos = adj['n_reclamos']
            lic.save(update_fields=[
                'monto_adjudicado', 'proveedor_adjudicado',
                'n_oferentes', 'url_acta', 'n_reclamos'])
            upd += 1
        self.stdout.write(self.style.SUCCESS(
            f'Backfill: {upd} actualizadas de {total} procesadas'))
