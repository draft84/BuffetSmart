from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.core.management import call_command

class Command(BaseCommand):
    help = (
        'Recorre de forma dinámica todos los esquemas definidos en settings.SCHEMAS, '
        'verifica que las migraciones labels.0001_initial, dishes.0001_initial y dishes.0002_preload_data '
        'estén marcadas como aplicadas (fake) si corresponde, y luego aplica la migración dishes.0003_week_restaurant.'
    )

    def handle(self, *args, **options):
        default_db = 'default'
        for schema in settings.SCHEMAS:
            self.stdout.write(f"\nProcesando esquema: {schema}")
            
            # Otorgar privilegios al usuario buffetsmart para el esquema actual.
            connection = connections[default_db]
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"GRANT ALL PRIVILEGES ON SCHEMA {schema} TO buffetsmart")
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error otorgando privilegios en el esquema {schema}: {e}"
                ))
                continue

            # Reconfiguramos la conexión para usar el search_path del esquema actual.
            connection.close()  # Cerramos para forzar la reapertura con nuevos parámetros.
            opts = connection.settings_dict.get('OPTIONS', {})
            opts['options'] = f"-c search_path={schema},public"
            connection.settings_dict['OPTIONS'] = opts

            # --- Verificar migración de labels.0001_initial ---
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM django_migrations WHERE app = %s AND name = %s",
                        ['labels', '0001_initial']
                    )
                    count = cursor.fetchone()[0]
                if count == 0:
                    self.stdout.write("No se encontró registro de labels.0001_initial; se marcará como aplicada (--fake).")
                    call_command('migrate', 'labels', '0001_initial', '--fake', database=default_db, verbosity=1)
                else:
                    self.stdout.write("labels.0001_initial ya está registrada, se continúa.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error verificando/marcando la migración labels en el esquema {schema}: {e}"
                ))
                continue

            # --- Verificar migración de dishes.0001_initial ---
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM django_migrations WHERE app = %s AND name = %s",
                        ['dishes', '0001_initial']
                    )
                    count = cursor.fetchone()[0]
                if count == 0:
                    self.stdout.write("No se encontró registro de dishes.0001_initial; se marcará como aplicada (--fake).")
                    call_command('migrate', 'dishes', '0001_initial', '--fake', database=default_db, verbosity=1)
                else:
                    self.stdout.write("dishes.0001_initial ya está registrada, se continúa.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error verificando/marcando la migración dishes.0001_initial en el esquema {schema}: {e}"
                ))
                continue

            # --- Verificar migración de dishes.0002_preload_data ---
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM django_migrations WHERE app = %s AND name = %s",
                        ['dishes', '0002_preload_data']
                    )
                    count = cursor.fetchone()[0]
                if count == 0:
                    self.stdout.write("No se encontró registro de dishes.0002_preload_data; se marcará como aplicada (--fake).")
                    call_command('migrate', 'dishes', '0002_preload_data', '--fake', database=default_db, verbosity=1)
                else:
                    self.stdout.write("dishes.0002_preload_data ya está registrada, se continúa.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error verificando/marcando la migración dishes.0002_preload_data en el esquema {schema}: {e}"
                ))
                continue

            # --- Aplicar la migración que agrega el campo foráneo en dishes ---
            try:
                call_command('migrate', 'dishes', '0003_week_restaurant', database=default_db, verbosity=1)
                self.stdout.write(self.style.SUCCESS(
                    f"Migración dishes.0003_week_restaurant aplicada correctamente en el esquema: {schema}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error aplicando migración dishes.0003_week_restaurant en el esquema {schema}: {e}"
                ))
