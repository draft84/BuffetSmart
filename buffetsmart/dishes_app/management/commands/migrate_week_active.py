# python manage.py migrate_week_active
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.core.management import call_command

class Command(BaseCommand):
    help = (
        "Recorre todos los esquemas en settings.SCHEMAS y aplica la migración "
        "0004_add_active_field_to_week (añade el campo `active` a Week) en cada uno."
    )

    def handle(self, *args, **options):
        default_db = 'default'
        for schema in settings.SCHEMAS:
            self.stdout.write(f"\n=== Procesando esquema: {schema} ===")
            
            # 1) Otorgar privilegios sobre el esquema (opcional, si lo necesitas)
            connection = connections[default_db]
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"GRANT ALL PRIVILEGES ON SCHEMA {schema} TO buffetsmart;")
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"[{schema}] No fue posible cambiar privilegios: {e}"
                ))
            
            # 2) Forzar reapertura de la conexión con el search_path apuntando al esquema
            connection.close()
            opts = connection.settings_dict.setdefault('OPTIONS', {})
            opts['options'] = f"-c search_path={schema},public"
            connection.settings_dict['OPTIONS'] = opts

            # 3) Aplicar la migración 0004_add_active_field_to_week
            try:
                call_command(
                    'migrate',
                    'dishes',
                    '0004_week_active',
                    database=default_db,
                    verbosity=1
                )
                self.stdout.write(self.style.SUCCESS(
                    f"[{schema}] Migración 0004_week_active aplicada correctamente."
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[{schema}] Error aplicando migración 0004: {e}"
                ))
