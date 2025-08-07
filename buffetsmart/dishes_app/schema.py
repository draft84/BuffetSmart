from django.db import connection
from .models import UserApp, Logs

from datetime import date, datetime, timedelta
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logger():
    fecha_actual = datetime.date.today().strftime('%Y-%m-%d')
    nombre_archivo = f"sincroni_log_{fecha_actual}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    manejador_archivo = TimedRotatingFileHandler(nombre_archivo, when='D', interval=1, backupCount=30)
    manejador_archivo.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger.addHandler(manejador_archivo)
    return logger

# Ejemplo de uso
logger = setup_logger()

# def set_schema(user):
    
#     print(user)

#     schema = UserApp.objects.filter(username=user.username).first()

#     if schema:
#         schema_name = schema.schema
#         with connection.cursor() as cursor:
#             cursor.execute(f'SET search_path TO {schema_name}')
#             Logs.objects.create(function = "set_schema", description = f"El esquema seleccionado es: {schema_name}", status = "Success") 
#             print(f"El esquema seleccionado es: {schema_name}")
#         return schema_name
#     else:
#         with connection.cursor() as cursor:
#             cursor.execute(f'SET search_path TO public;')
#             Logs.objects.create(function = "set_schema", description = "El esquema seleccionado es: public", status = "Error") 
#             print(f"El esquema seleccionado es: public")
#         return None

def set_schema(user, force_public=False):
    """
    Configura el esquema de base de datos.
    - Siempre usa 'public' si `user` es None, no está autenticado o `force_public` es True.
    """
    
    print(f"Usuario recibido en set_schema {user}")
    
    if force_public or user is None or not getattr(user, 'is_authenticated', False):
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO public;')
            Logs.objects.create(
                function="set_schema",
                description="Usuario no autenticado. Esquema configurado a 'public'.",
                status="Info"
            )
            print("Esquema configurado a 'public' (usuario no autenticado).")
        return None

    # Forzar esquema `public` para buscar en UserApp
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO public;')

    # Buscar esquema del usuario en public
    schema = UserApp.objects.filter(username=user.username).first()

    if schema:
        schema_name = schema.schema
        schema_id = schema.id
        schema_role = schema.role_id
        
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {schema_name}')

            print(f"Esquema configurado a: {schema_name}")
            logging.info(f"Esquema configurado a: {schema_name}")
            print(f"el id del esquema es: {schema_id}")
        return schema_name, schema_id, schema_role
    else:
        # Restaurar esquema a 'public' si no se encuentra el usuario
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO public;')

            print("Esquema configurado a 'public' (usuario no encontrado).")
        return None