# Correr el siguiente comando para migrar de forma masiva => python manage.py migrate_all_schemas, python manage.py migrate_specific_field, migrate_week_active, python manage.py migrate_menumanagement

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Create schemas, apply migrations, and load initial data'

    def handle(self, *args, **options):
        # Guardar la conexión actual
        default_db = connection.alias
        
        for schema in settings.SCHEMAS:
            self.stdout.write(f"Creating schema: {schema}")
            
            # Establecer el esquema actual
            with connection.cursor() as cursor:
                # Crear el esquema si no existe
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                
                # Otorgar todos los privilegios al usuario buffetsmart
                cursor.execute(f"GRANT ALL PRIVILEGES ON SCHEMA {schema} TO buffetsmart")

            self.stdout.write(self.style.SUCCESS(f"Successfully created schema: {schema} and granted privileges to buffetsmart"))

            # Aplicar migraciones
            self.stdout.write(f"Applying migrations to schema: {schema}")
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema}")

                # Aplicar migraciones
                call_command('migrate', database=default_db)

                # Cargar datos iniciales
                self.stdout.write(f"Loading initial data for schema: {schema}")
                # Aquí llamamos a la migración que carga los datos
                call_command('migrate', 'dishes', '0002_preload_data', database=default_db)

            self.stdout.write(self.style.SUCCESS(f"Successfully applied migrations and loaded data for schema: {schema}"))
