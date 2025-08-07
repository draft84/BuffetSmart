from dishes.schema import set_schema

class SchemaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            set_schema(request.user)
        else:
            set_schema(None)  # Configurar a 'public' si no está autenticado
        response = self.get_response(request)
        return response