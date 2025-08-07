# python manage.py migrate_menumanagement
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.core.management import call_command

class Command(BaseCommand):
    help = (
        "Recorre todos los esquemas de settings.SCHEMAS y aplica las migraciones "
        "pendientes de la app 'dishes' (incluyendo 0005_menumanagement)."
    )

    def handle(self, *args, **options):
        default_db = 'default'
        for schema in settings.SCHEMAS:
            self.stdout.write(f"\n=== Procesando esquema: {schema} ===")

            # 1) (Opcional) dar privilegios en el esquema
            conn = connections[default_db]
            try:
                with conn.cursor() as cursor:
                    cursor.execute(f"GRANT ALL PRIVILEGES ON SCHEMA {schema} TO postgres;")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"[{schema}] Warning al otorgar privilegios: {e}"))

            # 2) Forzar reapertura con search_path al esquema
            conn.close()
            opts = conn.settings_dict.setdefault('OPTIONS', {})
            opts['options'] = f"-c search_path={schema},public"
            conn.settings_dict['OPTIONS'] = opts

            # 3) Aplicar **todas** las migraciones de 'dishes'
            try:
                call_command(
                    'migrate',
                    'dishes',
                    '0005_menumanagement',
                    database=default_db,
                    verbosity=1
                )
                self.stdout.write(self.style.SUCCESS(f"[{schema}] Migraciones de 'dishes' aplicadas correctamente."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{schema}] Error al migrar 'dishes': {e}"))
