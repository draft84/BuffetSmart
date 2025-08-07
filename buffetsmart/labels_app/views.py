from rest_framework import viewsets
from .models import Pagination, Restaurant, Label, Template
from .serializers import RestaurantSerializer, LabelSerializer, TemplateSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from dishes.mixins import SchemaMixin
from rest_framework import filters
from dishes.schema import set_schema
from dishes.utils import schema_context

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de restaurantes
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class RestaurantViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de labels
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class LabelViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['label']
    ordering_fields  = ['label']
    ordering = ['label']
    
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de templates
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# class TemplateViewSet(SchemaMixin, viewsets.ModelViewSet):
#     # permission_classes = [IsAuthenticated]
#     queryset = Template.objects.all()
#     serializer_class = TemplateSerializer
    
    
class TemplateViewSet(SchemaMixin, viewsets.ModelViewSet):
    serializer_class = TemplateSerializer
    queryset = Template.objects.all()
    
    def get_queryset(self):
        # Establece el esquema y captura la información retornada.
        # set_schema devuelve (schema_name, schema_id, schema_role) o None.
        schema_name, schema_id, schema_role = set_schema(self.request.user)
        
        # Filtrado según el prefijo del esquema
        if schema_name.startswith('bs_'):
            queryset = Template.objects.filter(name__icontains='BLUESEA')
        elif schema_name.startswith('bf_'):
            queryset = Template.objects.filter(name__icontains='BARCELO')
        elif schema_name.startswith('kp_'):
            queryset = Template.objects.filter(name__icontains='KIMPTON')
        elif schema_name.startswith('lp_'):
            queryset = Template.objects.filter(name__icontains='LOPESAN')
            
        return queryset
