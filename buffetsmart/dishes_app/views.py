from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ModelViewSet
from .models import Pagination, Organization, Role, UserApp, Language, Dishes, DishesLang, Allergens, AllergensLang, Recipe, Time, Week, Assignment, MenuManagement, Exception
from labels.models import Label
from .utils import delete_menu, restore_dish_assignment, export_dishes_excel, bulk_upsert_assignments, get_valid_solum_token, setup_logger, store_code, serializers_hour_zone, user_list, get_deepl_target_languages, assignment_template, load_labels_template, list_schemas, schemas_list, traductor_masivo, add_update_solum, send_email, get_dish_exceptions, sync_labels_of_solum, sync_template_of_solum, labels_template, mac_adderss_list, solum_token_generate, install_product_labels, restore_dish, clear_dish, calculate_compliance, solum_gateway, labels_regenerate, patch_request, get_dish_exceptions, obtener_datos_dishes, obtener_times, change_hotel, list_hotel, create_translations, delete_exception, save_translations, labels_status, read_exception, edit_exception, store_code, export_assignments_to_excel, process_menu_assignments
from .schema import set_schema
from .serializers import CustomTokenObtainPairSerializer, OrganizationSerializer, RoleSerializer, UserSerializer, LanguageSerializer, DishesSerializer, DishesLangSerializer, DishesLangEditSerializer, AllergensSerializer, AllergenLangEditSerializer, RecipeSerializer, TimeSerializer, WeekSerializer, AssignmentSerializer, MenuManagementSerializer, ExceptionSerializer, OnlyDishesSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import IsAuthenticated
from .mixins import SchemaMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
import json
import unicodedata
from django.db.models import F, Value, Q, CharField
from django.db.models.functions import Lower, Replace
from googletrans import Translator, LANGUAGES
translator = Translator()
import time
from apscheduler.schedulers.background import BackgroundScheduler
from django.http import HttpResponse

from rest_framework_simplejwt.views import TokenObtainPairView

from django.db import transaction
from dishes.utils import schema_context

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

# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return response

# Scheduler
def start_scheduler(request):
    scheduler = BackgroundScheduler()
    # scheduler.add_job(labels_template, 'interval', minutes=1)
    scheduler.add_job(labels_template, 'cron', hour='5,10,11,17', minute='0,30,30,0')
    scheduler.start()
    return HttpResponse("Scheduler started")

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------- CREAR IDIOMAS ROLES Y USUARIOS ---------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
   
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de organizacion
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class OrganizationViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de roles
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class RoleViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de user
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = UserApp.objects.all()
    serializer_class = UserSerializer
    
    def destroy(self, request, *args, **kwargs):
        # Obtiene la instancia a eliminar
        instance = self.get_object()

        # Obtiene el serializador (no es obligatorio pasar la instancia, pero es buena práctica)
        serializer = self.get_serializer(instance)

        # Llama al método delete del serializador
        serializer.delete(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)

class LoginView(APIView):
    def post(self, request):
        
        username = request.data.get('username')
        
        password = make_password('password')

        try:
            user = UserApp.objects.get(username=username)
        except UserApp.DoesNotExist:
            return Response({"error": "Credenciales inválidas."}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si la contraseña proporcionada coincide con la contraseña encriptada almacenada
        if check_password(password, user.password):
            return Response({"error": "Credenciales inválidas."}, status=status.HTTP_400_BAD_REQUEST)

        # Generar token JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Si las credenciales son válidas, obtener los datos del usuario y sus roles
        serializer = UserSerializer(user)
        
        return Response({
            'user': serializer.data,
            'access_token': access_token,
        }, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de idiomas
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class LanguageViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de asignaciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
def normalize_term(term: str) -> str:
    return unicodedata.normalize('NFKD', term) \
                     .encode('ASCII', 'ignore') \
                     .decode('utf-8') \
                     .lower()

def normalize_expr(field):
    # 1) Lower siempre devuelve CharField
    expr = Lower(field, output_field=CharField())
    # 2) Cada Replace también devuelve CharField
    for accented, plain in [
        ('á','a'),('é','e'),('í','i'),
        ('ó','o'),('ú','u'),
        ('Á','a'),('É','e'),('Í','i'),
        ('Ó','o'),('Ú','u'),
    ]:
        expr = Replace(
            expr,
            Value(accented),
            Value(plain),
            output_field=CharField()
        )
    return expr

class OnlyDishesViewSet(SchemaMixin, ModelViewSet):
    queryset = Dishes.objects.all()
    serializer_class = OnlyDishesSerializer
    pagination_class = Pagination

    def get_queryset(self):
        qs = super().get_queryset().order_by('dish')
        term = self.request.query_params.get('search')
        if not term:
            return qs

        term_norm = normalize_term(term)

        return (
            qs
            .annotate(dish_plain=normalize_expr(F('dish')))
            .filter(dish_plain__icontains=term_norm)
        )

class DishesViewSet(SchemaMixin, ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Dishes.objects.all()
    serializer_class = DishesSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dish']
    ordering_fields  = ['dish']
    ordering = ['dish']
    
    # def perform_update(self, serializer):
    #     with transaction.atomic():
    #         transaction.on_commit(lambda: set_schema(self.request.user))
    #         print("Perform update: esquema establecido")
    #         super().perform_update(serializer)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista para editar idiomas de los platos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class DishesLangViewSet(SchemaMixin, viewsets.ModelViewSet):
    queryset = DishesLang.objects.all()
    serializer_class = DishesLangSerializer
    
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dish']
    ordering_fields  = ['dish']
    ordering = ['dish']
    
    def perform_create(self, serializer):
        with schema_context(self.request.user):
            super().perform_create(serializer)
            
    def perform_update(self, serializer):
        with schema_context(self.request.user):
            super().perform_update(serializer)

    def perform_destroy(self, instance):
        with schema_context(self.request.user):
            super().perform_destroy(instance)

class DishesLangEditViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = DishesLang.objects.all()
    serializer_class = DishesLangEditSerializer
    
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dish']
    ordering_fields  = ['dish']
    ordering = ['dish']

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de alergenos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AllergensViewSet(SchemaMixin, ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Allergens.objects.all()  # Queryset vacío para evitar evaluación temprana
    serializer_class = AllergensSerializer

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista para editar idiomas de los alergenos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AllergenLangEditViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = AllergensLang.objects.all()
    serializer_class = AllergenLangEditSerializer

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de recipes
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class RecipeViewSet(SchemaMixin, viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    
    def perform_create(self, serializer):
        with schema_context(self.request.user):
            super().perform_create(serializer)
            
    def perform_update(self, serializer):
        with schema_context(self.request.user):
            super().perform_update(serializer)

    def perform_destroy(self, instance):
        with schema_context(self.request.user):
            super().perform_destroy(instance)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de horarios
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class TimeViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Time.objects.all()
    serializer_class = TimeSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['restaurant', 'start']

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de semanas
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class WeekViewSet(SchemaMixin, viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = Week.objects.all()
    serializer_class = WeekSerializer
   

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de asignaciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------    
class AssignmentViewSet(SchemaMixin, viewsets.ModelViewSet):
    queryset = Assignment.objects.select_related('dish', 'week', 'label', 'time').all()  # Usa los nombres correctos de los campos
    serializer_class = AssignmentSerializer
    
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dish']
    ordering_fields  = ['dish']
    ordering = ['dish']
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        'label__restaurant': ['exact'],
        # 'dish': ['exact'],  # Campo en la tabla relacionada Dishes
        'week': ['exact'],  # Campo en la tabla Week
        'time': ['exact'],  # Campo en la tabla Time
    }
    
    def dispatch(self, request, *args, **kwargs):
        with schema_context(request.user):
            return super().dispatch(request, *args, **kwargs)
        
    def get_queryset(self):
        with transaction.atomic():
            set_schema(self.request.user)
            return super().get_queryset()

    def perform_create(self, serializer):
        with schema_context(self.request.user):
            super().perform_create(serializer)

    def perform_update(self, serializer):
        with schema_context(self.request.user):
            super().perform_update(serializer)

    def perform_destroy(self, instance):
        with schema_context(self.request.user):
            super().perform_destroy(instance)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista gestion de menu
# --------------------------------------------------------------------------------------------------------------------------------------------------------------    
class MenuManagementViewSet(SchemaMixin, viewsets.ModelViewSet):
    queryset = MenuManagement.objects.select_related('dish', 'week', 'label', 'time').all()  # Usa los nombres correctos de los campos
    serializer_class = MenuManagementSerializer
    
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dish']
    ordering_fields  = ['dish']
    ordering = ['dish']
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        'label__restaurant': ['exact'],
        # 'dish': ['exact'],  # Campo en la tabla relacionada Dishes
        'week': ['exact'],  # Campo en la tabla Week
        'time': ['exact'],  # Campo en la tabla Time
    }
    
    def dispatch(self, request, *args, **kwargs):
        with schema_context(request.user):
            return super().dispatch(request, *args, **kwargs)
        
    def get_queryset(self):
        with transaction.atomic():
            set_schema(self.request.user)
            return super().get_queryset()

    def perform_create(self, serializer):
        with schema_context(self.request.user):
            super().perform_create(serializer)

    def perform_update(self, serializer):
        with schema_context(self.request.user):
            super().perform_update(serializer)

    def perform_destroy(self, instance):
        with schema_context(self.request.user):
            super().perform_destroy(instance)        

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Crear asignaciones para gestionar un nuevo menu
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class MenuAssignmentView(APIView):
    """
    Endpoint para crear asignaciones de menú.
    """
    def post(self, request, *args, **kwargs):
        # request.user debe usarse para seleccionar esquema
        result, code = process_menu_assignments(request.user, request.data)
        return Response(result, status=code)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Salvar la gestion en la tabla asignaciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AssignFromTimeView(APIView):
    """
    Endpoint para copiar todas las asignaciones existentes en MenuManagement
    para un time_id dado hacia la tabla Assignment.
    """
    def post(self, request, *args, **kwargs):
        set_schema(request.user)
        time_id = request.data.get('time_id')
        if not time_id:
            return Response({'detail': 'time_id es obligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validar que exista el Time
        try:
            time_obj = Time.objects.get(id=time_id)
        except Time.DoesNotExist:
            return Response({'detail': 'Time no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Obtener asignaciones en MenuManagement
        menu_items = MenuManagement.objects.filter(time=time_obj)
        if not menu_items.exists():
            return Response({'detail': 'No hay asignaciones en MenuManagement para ese time_id.'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear registros en Assignment
        assignments = []
        for item in menu_items:
            assignments.append(
                Assignment(
                    dish=item.dish,
                    week=item.week,
                    label=item.label,
                    time=item.time,
                    day_of_week=item.day_of_week
                )
            )
        Assignment.objects.bulk_create(assignments)

        return Response({'detail': f'Se han copiado {len(assignments)} asignaciones a Assignment.'}, status=status.HTTP_201_CREATED)
      
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista de excepciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
from datetime import datetime, timedelta
from rest_framework.exceptions import ValidationError
class ExceptionViewSet(SchemaMixin, viewsets.ModelViewSet):
    queryset = Exception.objects.select_related("dish", "assignment", "week", "time").all()
    serializer_class = ExceptionSerializer
    pagination_class = Pagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dish']
    ordering_fields = ['dish']
    ordering = ['dish']
    filterset_fields = {
        'date': ['exact'],
        'week_id': ['exact'],
        'time_id': ['exact'],
    }

    def get_queryset(self):
        qs = super().get_queryset()
        # 1) Si NO es la acción de list, devolvemos TODO el queryset
        if self.action not in ('list',):
            return qs

        # 2) Sólo para list(), aplicamos el filtro semanal + opcional de time/week
        today  = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        week_id = self.request.query_params.get('week_id')
        time_id = self.request.query_params.get('time_id')

        if week_id is not None:
            qs = qs.filter(week_id=week_id)
        if time_id is not None:
            qs = qs.filter(time_id=time_id)

        return qs.filter(date__gte=monday, date__lte=sunday)
    
    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        user = self.request.user  # Obtiene el usuario de la solicitud
        exception = serializer.save(user=user)  # Pasa el usuario al serializador si es necesario
        return exception

    def perform_update(self, serializer):
        serializer.is_valid(raise_exception=True)
        user = self.request.user  # Obtiene el usuario de la solicitud
        exception = serializer.save(user=user)  # Pasa el usuario al serializador si es necesario
        return exception

    def perform_destroy(self, instance):
        user = self.request.user  # Obtiene el usuario de la solicitud
        print(f"Eliminando la excepción por el usuario: {user.username}")
        instance.delete()  # Elimina la instancia

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista para mostar los labels con status true de solum
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class SyncSolumLabelsView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, mac_address):
        messages = sync_labels_of_solum(mac_address, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista para mostar los labels con status true de solum
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class SyncSolumTemplateView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        messages = sync_template_of_solum(request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Crear producto y asignacion a partir de los labels con nomneclarura asignada
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class InstallView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        messages = install_product_labels(request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Listar teplate disponibles
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ListTemplateView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        list_template = load_labels_template(request.user)  # Llama a la función list_hotel
        return Response({"data": json.loads(list_template)}, status=status.HTTP_200_OK)
        
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Asignar template
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AssignmentTemplateView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, template, mac=None):
        messages = assignment_template(request.user, template, mac if mac else None)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la vista para mostar los labels con status true de solum
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class LabelsScheduleView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, restaurant=None):
        messages = labels_template(request.user, restaurant if restaurant else None)
        return Response({"messages": messages}, status=status.HTTP_200_OK)       

class LabelsStatusViews(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, lbl_status):
        # Extraer los parámetros de paginación y búsqueda desde la query string
        try:
            page = int(request.query_params.get('page', 1))
        except ValueError:
            page = 1

        try:
            page_size = int(request.query_params.get('page_size', 10))
        except ValueError:
            page_size = 10

        search = request.query_params.get('search', None)

        # Llamar a la función labels_status pasando request.user, lbl_status y los parámetros adicionales
        labels_data = labels_status(
            request.user,
            lbl_status,
            page=page,
            page_size=page_size,
            search=search
        )

        return Response({"labels_status": labels_data}, status=status.HTTP_200_OK)
        
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Cargamos el listado de mac
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class MacListView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        messages = mac_adderss_list(request.user)
        return Response({"macAddress": messages}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Generar token
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class TokenView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        data = solum_token_generate(request.user)
        return Response({"access_token": data}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------   
# Cumplimiento de menu
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class MenuComplianceView(SchemaMixin, APIView):
    def get(self, request, start_date, end_date, turn=None):
        try:
            # Si turn está vacío, puedes pasarlo como None
            result = calculate_compliance(start_date, end_date, turn if turn else None, request.user)
            print(f"Vista - Resultado: {result}")
            return Response({"messages": result}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error en la vista: {str(e)}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# --------------------------------------------------------------------------------------------------------------------------------------------------------------   
# Menu de cumplimiento lista
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class TotalExceptionAssignmentsView(SchemaMixin, APIView):
    def get(self, request, start_date, end_date, turn=None):
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 10)), 100)
        
        search = request.GET.get('search', None)
        ordering = request.GET.get('ordering', None)
        
        results, total = get_dish_exceptions(
            start_date=start_date,
            end_date=end_date,
            turn=turn,
            user=request.user,
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering
        )
        
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "messages": results
        })

# --------------------------------------------------------------------------------------------------------------------------------------------------------------   
# Cumplimiento de menu
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ExceptionDetailsView(SchemaMixin, APIView):
    def get(self, request, start_date, end_date, turn=None):
        messages = get_dish_exceptions(start_date, end_date, turn if turn else None, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------   
# Restore dish
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class RestDishView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, day_of_week, articleId, dish_id, time_id):
        messages = restore_dish(day_of_week, articleId, dish_id, time_id, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
    
class RestDishAssignmentView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, day_of_week, articleId, dish_id, time_id):
        messages = restore_dish_assignment(day_of_week, articleId, dish_id, time_id, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
        
class DeleteExceptionView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, day_of_week, articleId, dish_id, time_id):
        messages = delete_exception(day_of_week, articleId, dish_id, time_id, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------   
# Clear dish
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class RestArticleView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, articleId):
        messages = clear_dish(articleId, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Send email
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class SendEmailView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        sender_email = request.data.get('sender_email')
        hotel_name = request.data.get('hotel_name')
        title_email = request.data.get('title_email')
        mensaje_email = request.data.get('mensaje_email')

        if not sender_email or not title_email or not mensaje_email:
            return Response({"error": "Faltan datos requeridos."}, status=status.HTTP_400_BAD_REQUEST)

        messages = send_email(sender_email, title_email, mensaje_email, hotel_name)  # Asegúrate de que send_email acepte estos parámetros
        return Response({"messages": messages}, status=status.HTTP_200_OK)

class DeeplLanguagesView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            languages = get_deepl_target_languages()
            return Response(languages, status=status.HTTP_200_OK)
        except request.exceptions.HTTPError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class TranslatePreviewViews(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, dish):
        translations = create_translations(request.user, dish)
        return Response({"translations": json.loads(translations)}, status=status.HTTP_200_OK)
    
class TranslateSavedViews(SchemaMixin, APIView):
    def post(self, request):
        # Obtener los datos enviados en el cuerpo del request
        dish = request.data.get("dish")
        trans_1 = request.data.get("trans_1")
        trans_2 = request.data.get("trans_2")
        trans_3 = request.data.get("trans_3")
        trans_4 = request.data.get("trans_4")
        code_1 = request.data.get("code_1")
        code_2 = request.data.get("code_2")
        code_3 = request.data.get("code_3")
        code_4 = request.data.get("code_4")
        allergen_ids = request.data.get("allergen_ids", [])
        all_schemas_is_verified = request.data.get("all_schemas_is_verified", False)

        # Validar que el parámetro "dish" esté presente
        if not dish:
            return Response(
                {"error": "El campo 'dish' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Llamar a la función save_translations
        translations = save_translations(request.user, dish, trans_1, trans_2, trans_3, trans_4, code_1, code_2, code_3, code_4, allergen_ids, all_schemas_is_verified)
        
        return Response(
            json.loads(translations),
            status=status.HTTP_200_OK
        )
        
class ListSchemaView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        hotels = list_schemas(request.user)  # Llama a la función list_hotel
        return Response({"schemas_list": json.loads(hotels)}, status=status.HTTP_200_OK)
    
class UserListView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        users = user_list(request.user)  # Llama a la función list_hotel
        return Response(json.loads(users), status=status.HTTP_200_OK)
        
class SchemasListView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        schema_list = schemas_list(request.user)
        return Response({"schemas_list": json.loads(schema_list)}, status=status.HTTP_200_OK)

class ListHotelView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        hotels = list_hotel(request.user)  # Llama a la función list_hotel
        return Response({"hotel_list": json.loads(hotels)}, status=status.HTTP_200_OK)

class ChangeHotelView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, userID):
        messages = change_hotel(request.user, userID)
        return Response({"change_hotels": json.loads(messages)}, status=status.HTTP_200_OK)
    
class GatewayView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        messages = solum_gateway(request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
        
class LabelGatewayView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        messages = labels_regenerate(request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
        
class PatchGatewayView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, solum_gateway):
        messages = patch_request(solum_gateway, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------   
# Actualizacion de producto en solum
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class UpdateProductSolumView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, dish_id, label_id):
        messages = add_update_solum(dish_id, label_id, request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

class HotelScheduleView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, username, password, restID=None):
        messages = obtener_datos_dishes(username, password, restID if restID else None)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
    
class TimesScheduleView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, username, password):
        messages = obtener_times(username, password)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
    
# traductor masivo
class TraductorMasivoView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        messages = traductor_masivo(request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)

class CopyHorizontalAssignmentsView(SchemaMixin, APIView):
    
    def post(self, request, label_value):
        
        set_schema(self.request.user)
        
        print(f"El label a editar es el {label_value}")
        
        l = Label.objects.filter(label=label_value).first()

        if l is None:
            return Response({"error": "Label not found"}, status=status.HTTP_404_NOT_FOUND)

        # Obtener el array de asignaciones del request
        assignments_data = request.data

        # Iterar sobre el array de asignaciones
        for assignment_data in assignments_data:
            
            print(f"Asignacion: day_of_week=>{assignment_data['day_of_week']}, label_id=>{l.id}, dish_id=>{assignment_data['dish_id']}, time_id=>{assignment_data['time']}, week_id=>{assignment_data['week']}")
            
            # Buscar todas las asignaciones con el label correspondiente
            assignments = Assignment.objects.filter(day_of_week=assignment_data['day_of_week'], label=l.id, time_id=assignment_data['time'], week_id=assignment_data['week']).update(dish_id=assignment_data['dish_id'])

        return Response({"message": "Assignments updated successfully"}, status=status.HTTP_200_OK)
    
class CopyVerticalAssignmentsView(SchemaMixin, APIView):
    
    def post(self, request, day_value):
        
        set_schema(self.request.user)
        
        print(f"El day_of_week a editar es el {day_value}")

        # Obtener el array de asignaciones del request
        assignments_data = request.data

        # Iterar sobre el array de asignaciones
        for assignment_data in assignments_data:
            
            print(f"Asignacion: day_of_week=>{day_value}, label_id=>{assignment_data['label']}, dish_id=>{assignment_data['dish_id']}, time_id=>{assignment_data['time']}, week_id=>{assignment_data['week']}")
            
            # Buscar todas las asignaciones con el label correspondiente
            assignments = Assignment.objects.filter(day_of_week=day_value, label=assignment_data['label'], time_id=assignment_data['time'], week_id=assignment_data['week']).update(dish_id=assignment_data['dish_id'])

        return Response({"message": "Assignments updated successfully"}, status=status.HTTP_200_OK)
    
class CopyExceptionView(SchemaMixin, APIView):
    
    def post(self, request):
        set_schema(self.request.user)

        exception_data = request.data  # Se asume que esto es una lista de diccionarios

        for e in exception_data:
            exception_id = e.get('id')  # Obtener el ID del elemento actual

            if exception_id:
                # Intentar actualizar la excepción existente
                try:
                    exception = Exception.objects.get(id=exception_id)
                    # Actualizar los campos de la excepción
                    exception.date = e.get('date', exception.date)
                    exception.assignment_id = e.get('assignment', exception.assignment_id)
                    exception.dish_id = e.get('dish', exception.dish_id)
                    exception.label_id = e.get('label', exception.label_id)
                    exception.time_id = e.get('time', exception.time_id)
                    exception.week_id = e.get('week', exception.week_id)
                    exception.save()  # Guardar los cambios
                except Exception.DoesNotExist:
                    return Response({
                        "error": f"Exception with id {exception_id} does not exist.",
                        "data": exception_data
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Crear una nueva excepción si no se proporciona un ID
                try:
                    exception = Exception.objects.create(
                        date=e.get('date'),
                        assignment_id=e.get('assignment'),
                        dish_id=e.get('dish'),
                        label_id=e.get('label'),
                        time_id=e.get('time'),
                        week_id=e.get('week'),
                    )
                    
                except Exception as e:
                    return Response({
                        "error": f"Error creating exception: {str(e)}",
                        "data": exception_data
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        messages=[]
        
        token_data = get_valid_solum_token(self.request.user)
        if not token_data:
            messages.append("No se pudo obtener un token válido")
            return messages

        # Extrae el access_token y company desde token_data
        access_token = token_data['access_token']

        time.sleep(3)
        status_code = read_exception(access_token, self.request.user)
                    
        if status_code == 200:
            return Response({"message": "Assignments processed successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Error de conexion con solum al leer la excepciones", "status": status_code, "array":exception_data})

class CopyHorizontalAssignmentsMagnamentView(SchemaMixin, APIView):
    
    def post(self, request, label_value):
        
        set_schema(self.request.user)
        
        print(f"El label a editar es el {label_value}")
        
        l = Label.objects.filter(label=label_value).first()

        if l is None:
            return Response({"error": "Label not found"}, status=status.HTTP_404_NOT_FOUND)

        # Obtener el array de asignaciones del request
        assignments_data = request.data

        # Iterar sobre el array de asignaciones
        for assignment_data in assignments_data:
            
            print(f"Asignacion: day_of_week=>{assignment_data['day_of_week']}, label_id=>{l.id}, dish_id=>{assignment_data['dish_id']}, time_id=>{assignment_data['time']}, week_id=>{assignment_data['week']}")
            
            # Buscar todas las asignaciones con el label correspondiente
            assignments = MenuManagement.objects.filter(day_of_week=assignment_data['day_of_week'], label=l.id, time_id=assignment_data['time'], week_id=assignment_data['week']).update(dish_id=assignment_data['dish_id'])

        return Response({"message": "Assignments updated successfully"}, status=status.HTTP_200_OK)
    
class CopyVerticalAssignmentsMagnamentView(SchemaMixin, APIView):
    
    def post(self, request, day_value):
        
        set_schema(self.request.user)
        
        print(f"El day_of_week a editar es el {day_value}")

        # Obtener el array de asignaciones del request
        assignments_data = request.data

        # Iterar sobre el array de asignaciones
        for assignment_data in assignments_data:
            
            print(f"Asignacion: day_of_week=>{day_value}, label_id=>{assignment_data['label']}, dish_id=>{assignment_data['dish_id']}, time_id=>{assignment_data['time']}, week_id=>{assignment_data['week']}")
            
            # Buscar todas las asignaciones con el label correspondiente
            assignments = MenuManagement.objects.filter(day_of_week=day_value, label=assignment_data['label'], time_id=assignment_data['time'], week_id=assignment_data['week']).update(dish_id=assignment_data['dish_id'])

        return Response({"message": "Assignments updated successfully"}, status=status.HTTP_200_OK)

class ExceptionMultipleView(SchemaMixin, APIView):
    def post(self, request):
        if request.user.is_authenticated:
            set_schema(self.request.user)
            
            messages=[]
            
            token_data = get_valid_solum_token(self.request.user)
            if not token_data:
                messages.append("No se pudo obtener un token válido")
                return messages

            access_token = token_data['access_token']
                    
            # Asegúrate de que read_exception no altere el esquema
            with schema_context(self.request.user):
                exception_data = request.data
                        
                # Iterar sobre el array de asignaciones
                for e in exception_data:
                    # Validar si ya existe un registro con los mismos valores
                    exists = Exception.objects.filter(
                        date=e['date'],
                        assignment_id=e['assignment'],
                        label_id=e['label'],
                        time_id=e['time'],
                        week_id=e['week']
                    ).exists()
                            
                    if exists:
                        Exception.objects.filter(
                            date=e['date'],
                            assignment_id=e['assignment'],
                            label_id=e['label'],
                            time_id=e['time'],
                            week_id=e['week']
                        ).update(
                            dish_id=e['dish']
                        )
                    else:
                        # Crear excepciones si no existe
                        Exception.objects.create(
                            date=e['date'],
                            assignment_id=e['assignment'],
                            dish_id=e['dish'],
                            label_id=e['label'],
                            time_id=e['time'],
                            week_id=e['week']
                        )

                time.sleep(3)
                status_code = read_exception(access_token, self.request.user)
                        
                print(status_code)
                        
                if status_code == 200:
                    return Response({"message": "Exception created and processed successfully"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Exception created but failed to process"}, status=status_code)

            return Response({"message": "Exception created successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

class HourZonetView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        messages = serializers_hour_zone(request.user)
        return Response({"messages": messages}, status=status.HTTP_200_OK)
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Exportar a excel
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ExportExcelView(SchemaMixin, APIView):
    def get(self, request, week_id):
        return export_assignments_to_excel(request.user, week_id)
    
class ExportDishesView(SchemaMixin, APIView):
    def get(self, request):
        return export_dishes_excel(request.user)
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Crear menu
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class CreateMenuView(SchemaMixin, APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        result = bulk_upsert_assignments(request, request.user)
        return Response(result, status=result.get('status', status.HTTP_200_OK))

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Eliminar menu de gestion
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class DeleteMenuAssignmentView(APIView):

    def get(self, request, restaurant_id):
        # request.user debe usarse para seleccionar esquema
        result, code = delete_menu(request.user, restaurant_id)
        return Response(result, status=code)