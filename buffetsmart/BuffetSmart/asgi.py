# import os
# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buffetsmart.settings')  # Reemplaza 'your_project' por el nombre real de tu proyecto

# application = get_asgi_application()


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buffetsmart.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # Agrega otras configuraciones si es necesario
})