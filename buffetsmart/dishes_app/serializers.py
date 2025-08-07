from rest_framework import serializers
import requests
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Organization, Role, UserApp, Language, Dishes, DishesLang, Allergens, AllergensLang, Recipe, Time, Week, Assignment, MenuManagement, Exception, Permission
from labels.models import Restaurant
from django.contrib.auth.hashers import make_password
import deepl
import json

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .utils import set_schema, create_organization, hour_zone, store_code, solum_token_generate, sync_labels_of_solum, add_exception, edit_exception

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

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Aquí tienes acceso al usuario
        set_schema(self.user)
        return data
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Importamos los modelos de labels
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
from labels.models import Label
from labels.serializers import LabelSerializer

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# importamos las librerias de google para la traduccion
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
from googletrans import Translator
from googletrans import LANGUAGES

translator = Translator()

from django.contrib.auth.models import User as DjangoUser

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------- CREAR IDIOMAS ROLES Y USUARIOS ---------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de organizacion
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de roles
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Permisos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de user
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
from django.contrib.auth.hashers import make_password, check_password

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer()
    organization = OrganizationSerializer()
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserApp
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = RoleSerializer(instance.role).data
        return representation

    def create(self, validated_data):
        role_data = validated_data.pop('role')
        organization_data = validated_data.pop('organization')
        
        # Crear la instancia de organización
        organization_serializer = OrganizationSerializer(data=organization_data)
        organization_serializer.is_valid(raise_exception=True)
        organization = organization_serializer.save()

        # Hashear la contraseña
        password = validated_data.pop('password')
        hashed_password = make_password(password)

        role, created = Role.objects.get_or_create(**role_data)

        user = UserApp.objects.create(
            role=role,
            organization=organization,
            password=hashed_password,
            **validated_data
        )

        # Crear superusuario de Django con el mismo usuario y contraseña
        django_user_data = {
            'username': validated_data['username'],
            'password': password,
            'is_superuser': True,
            'is_staff': True
        }
        DjangoUser.objects.create_superuser(**django_user_data)

        create_organization(
            user=validated_data['username'],
            organization=organization_data['name'],
            company=organization_data['company'],
            store_code=organization_data['store_code']
        )
        return user

    def update(self, instance, validated_data):
        # Extraer datos anidados y el password (para procesarlo aparte)
        role_data = validated_data.pop('role', None)
        organization_data = validated_data.pop('organization', None)
        new_password = validated_data.pop('password', None)
        
        # Guardar el username actual para compararlo luego
        old_username = instance.username

        # Actualizar los demás campos proporcionados
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if organization_data:
            # Actualizar la instancia de la organización en lugar de crear una nueva
            organization_serializer = OrganizationSerializer(
                instance=instance.organization, 
                data=organization_data, 
                partial=True
            )
            organization_serializer.is_valid(raise_exception=True)
            organization_serializer.save()

        if role_data:
            role, created = Role.objects.get_or_create(**role_data)
            instance.role = role

        instance.save()

        # Actualizar el username en DjangoUser si fue modificado
        new_username = instance.username
        if new_username != old_username:
            try:
                django_user = DjangoUser.objects.get(username=old_username)
                django_user.username = new_username
                django_user.save()
            except DjangoUser.DoesNotExist:
                pass

        # Procesar el password: solo si se envía y es distinto al actual
        if new_password:
            if not check_password(new_password, instance.password):
                instance.password = make_password(new_password)
                instance.save(update_fields=['password'])
                try:
                    django_user = DjangoUser.objects.get(username=new_username)
                    django_user.set_password(new_password)
                    django_user.save()
                except DjangoUser.DoesNotExist:
                    pass

        return instance

    def delete(self, instance):
        print(f"Eliminando usuario: {instance.username}")
        if instance.organization:
            print(f"Eliminando organización: {instance.organization.name}")
            instance.organization.delete()
        
        django_user = DjangoUser.objects.filter(username=instance.username).first()
        if django_user:
            django_user.delete()
        
        instance.delete()

        
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de idiomas
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class LanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Language
        fields = '__all__'
    
    # def create(self, validated_data):
        
    #     auth_key = '5c16caf8-8b42-4789-83b3-25aca76925f7'  # Reemplaza con tu clave de autenticación
    #     translator = deepl.Translator(auth_key)
        
    #     # Crear el nuevo idioma
    #     language_instance = super().create(validated_data)
        
    #     language=language_instance.code
        
    #     dishes_lang_instances = []

    #     # Verificar si el idioma recién creado está activo
    #     if language_instance.status:
    #         # Obtener todos los platos
    #         dishes = Dishes.objects.all()

    #         # Traducir y registrar en DishesLang
    #         for dish in dishes:
                
    #             dishTranslate = translator.translate_text(dish.dish, target_lang=language)
    #             print(f"Code: {language} Plato a traducir: {dish.dish} Traducción: {dishTranslate.text}")

    #             # Crea una instancia de DishesLang para cada traducción
    #             dishes_lang_instances.append(DishesLang(dish=dish, language=language, translation=dishTranslate.text.upper()))
    #         # Inserta todas las traducciones en una sola operación
        
    #         DishesLang.objects.bulk_create(dishes_lang_instances)

    #    return language_instance

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------- PLATOS RECIPES Y ALEERGENOS -----------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
       
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de los platos en los idiomas deseados
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class DishesLangSerializer(serializers.ModelSerializer):
    class Meta:
        model = DishesLang
        fields = '__all__'
        
    def to_internal_value(self, data):
        """
        Sobreescribe la validación para asegurarse de que el esquema esté configurado
        antes de resolver cualquier queryset.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de alergenos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AllergensLangSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllergensLang
        fields = '__all__'

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de los alergenos en los idiomas deseados
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AllergensSerializer(serializers.ModelSerializer):
    allergenLang = AllergensLangSerializer(many=True, read_only=True)

    class Meta:
        model = Allergens
        fields = ['id', 'allergen', 'picture', 'allergenLang']
    
    def create(self, validated_data):
        instance = super().create(validated_data)
        self.translate_and_save(instance)
        return instance

    def update(self, instance, validated_data):
        instance.allergen = validated_data.get('allergen', instance.allergen)
        instance.picture = validated_data.get('picture', instance.picture)
        instance.save()
        self.translate_and_save(instance)
        return instance

    def translate_and_save(self, instance):
        
        translator = Translator()
        allergen_text = instance.allergen.lower()

        # Detecta el idioma del texto original
        detected_lang = translator.detect(allergen_text).lang

        # Obtiene los idiomas activos
        active_languages = Language.objects.filter(code='EN-US', status=True)

        # Traduce y guarda cada idioma activo en AllergensLang
        for language in active_languages:
            if detected_lang == language.code:
                continue

            try:
                auth_key = '5c16caf8-8b42-4789-83b3-25aca76925f7'  # Reemplaza con tu clave de autenticación
                translator = deepl.Translator(auth_key)
                
                translation = translator.translate_text(allergen_text, target_lang=language.code)
                AllergensLang.objects.update_or_create(
                    allergen=instance,
                    language=language,
                    defaults={'translation': translation.text.upper()}
                )
            except:
                print(f"Error al traducir a {language.code}")
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de alergenos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class DishesRecipeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Dishes
        fields = ['id','dish']
        
class RecipeSerializer(serializers.ModelSerializer):
    
    allergens = AllergensSerializer(many=True, read_only=True)

    # PrimaryKeyRelatedField normal, sin personalización
    allergen_ids = serializers.PrimaryKeyRelatedField(queryset=Allergens.objects.all(), many=True, write_only=True, source='allergens')

    dish = serializers.PrimaryKeyRelatedField(queryset=Dishes.objects.all(), write_only=True)

    dish_name = serializers.CharField(source='dish.dish', read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'dish', 'dish_name', 'allergens', 'allergen_ids')

    def to_internal_value(self, data):
        """
        Sobreescribe la validación para asegurarse de que el esquema esté configurado
        antes de resolver cualquier queryset.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------- ASIGNACION DE DISPONIBLILIDAD PARA LOS PLATOS --------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de horarios
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class TimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Time
        fields = '__all__'
        
    def to_internal_value(self, data):
        """
        Sobreescribe la validación para asegurarse de que el esquema esté configurado
        antes de resolver cualquier queryset.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de semanas
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class WeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Week
        fields = '__all__'
        
    def validate(self, attrs):
        """
        Validación personalizada para asegurarse de que no existan registros
        con el mismo start_date, end_date y restaurant_id.
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        restaurant_id = attrs.get('restaurant')

        # Obtener el ID del objeto actual si se está actualizando
        instance = self.instance

        # Verifica si ya existe un registro con los mismos valores, excluyendo el registro actual
        conflicting_weeks = Week.objects.filter(
            start_date=start_date,
            end_date=end_date,
            restaurant_id=restaurant_id
        )

        if instance:
            conflicting_weeks = conflicting_weeks.exclude(id=instance.id)

        if conflicting_weeks.exists():
            raise serializers.ValidationError("Las fechas y restaurant seleccionados para crear la rueda ya existe.")

        return attrs

    
    def to_internal_value(self, data):
        """
        Sobreescribe la validación para asegurarse de que el esquema esté configurado
        antes de resolver cualquier queryset.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de asignaciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AssignmentSerializer(serializers.ModelSerializer):
    
    dish_id = serializers.PrimaryKeyRelatedField(source='dish', queryset=Dishes.objects.all())  # Cambia 'dish' a 'dish_id'
    dish_name = serializers.CharField(source='dish.dish', read_only=True)  # Obtener el nombre del plato directamente

    week = serializers.PrimaryKeyRelatedField(queryset=Week.objects.all())
    time = serializers.PrimaryKeyRelatedField(queryset=Time.objects.all())
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all(), required=False, allow_null=True)

    times = serializers.SerializerMethodField()  # Si necesitas lógica adicional, puedes mantenerlo
    labels = serializers.SerializerMethodField()  # Lo mismo aquí

    class Meta:
        model = Assignment
        fields = ('id', 'dish_id', 'dish_name', 'week', 'label', 'time', 'day_of_week', 'times', 'labels')

    def get_times(self, obj):
        # Implementa la lógica para obtener los tiempos si es necesario
        return [time.id for time in obj.time_set.all()]  # Ajusta según tu modelo

    def get_labels(self, obj):
        # Implementa la lógica para obtener las etiquetas si es necesario
        return [label.id for label in obj.label_set.all()]  # Ajusta según tu modelo
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('times', None)
        representation.pop('labels', None)
        return representation

    def get_dish_name(self, obj):
        return obj.dish.dish

    def get_times(self, obj):
        return TimeSerializer(obj.time).data

    def get_labels(self, obj):
        if obj.label:
            return LabelSerializer(obj.label).data
        return None

    def update(self, instance, validated_data):
        # Actualizar otros campos directamente desde validated_data
        instance.week = validated_data.get('week', instance.week)
        instance.time = validated_data.get('time', instance.time)
        instance.label = validated_data.get('label', instance.label)

        # Actualizar dish directamente si está en validated_data
        # Cambiar 'dish_id' por 'dish' ya que 'dish_id' está mapeado a 'dish' en validated_data
        if 'dish' in validated_data:
            instance.dish = validated_data['dish']
            print(f"Dish: {validated_data['dish']}")

        # Guardar los cambios en la instancia
        instance.save()
        print(f"Instancia actualizada: {instance}")
        return instance
    
    def to_internal_value(self, data):
        """
        Sobreescribe la validación para asegurarse de que el esquema esté configurado
        antes de resolver cualquier queryset.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador para gestionar asignaciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class MenuManagementSerializer(serializers.ModelSerializer):
    
    dish_id = serializers.PrimaryKeyRelatedField(source='dish', queryset=Dishes.objects.all())  # Cambia 'dish' a 'dish_id'
    dish_name = serializers.CharField(source='dish.dish', read_only=True)  # Obtener el nombre del plato directamente

    week = serializers.PrimaryKeyRelatedField(queryset=Week.objects.all())
    time = serializers.PrimaryKeyRelatedField(queryset=Time.objects.all())
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all(), required=False, allow_null=True)

    times = serializers.SerializerMethodField()  # Si necesitas lógica adicional, puedes mantenerlo
    labels = serializers.SerializerMethodField()  # Lo mismo aquí

    class Meta:
        model = MenuManagement
        fields = ('id', 'dish_id', 'dish_name', 'week', 'label', 'time', 'day_of_week', 'times', 'labels')

    def get_times(self, obj):
        # Implementa la lógica para obtener los tiempos si es necesario
        return [time.id for time in obj.time_set.all()]  # Ajusta según tu modelo

    def get_labels(self, obj):
        # Implementa la lógica para obtener las etiquetas si es necesario
        return [label.id for label in obj.label_set.all()]  # Ajusta según tu modelo
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('times', None)
        representation.pop('labels', None)
        return representation

    def get_dish_name(self, obj):
        return obj.dish.dish

    def get_times(self, obj):
        return TimeSerializer(obj.time).data

    def get_labels(self, obj):
        if obj.label:
            return LabelSerializer(obj.label).data
        return None

    def update(self, instance, validated_data):
        # Actualizar otros campos directamente desde validated_data
        instance.week = validated_data.get('week', instance.week)
        instance.time = validated_data.get('time', instance.time)
        instance.label = validated_data.get('label', instance.label)

        # Actualizar dish directamente si está en validated_data
        # Cambiar 'dish_id' por 'dish' ya que 'dish_id' está mapeado a 'dish' en validated_data
        if 'dish' in validated_data:
            instance.dish = validated_data['dish']
            print(f"Dish: {validated_data['dish']}")

        # Guardar los cambios en la instancia
        instance.save()
        print(f"Instancia actualizada: {instance}")
        return instance
    
    def to_internal_value(self, data):
        """
        Sobreescribe la validación para asegurarse de que el esquema esté configurado
        antes de resolver cualquier queryset.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de excepciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class ExceptionSerializer(serializers.ModelSerializer):
    dish = serializers.PrimaryKeyRelatedField(queryset=Dishes.objects.all())
    week = serializers.PrimaryKeyRelatedField(queryset=Week.objects.all(), required=False, allow_null=True)
    time = serializers.PrimaryKeyRelatedField(queryset=Time.objects.all(), required=False, allow_null=True)
    assignment = serializers.PrimaryKeyRelatedField(queryset=Assignment.objects.all())
    labels = serializers.SerializerMethodField()

    class Meta:
        model = Exception
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('labels', None)
        return representation
        
    def get_labels(self, obj):
        label = obj.label
        return LabelSerializer(label).data if label else None

    def create(self, validated_data):
        
        user = validated_data.pop('user', None)
        
        # Extraer los campos necesarios del diccionario de datos validados
        assignment = validated_data.pop('assignment')
        dish = validated_data.pop('dish')  # Extraer el dish de los datos validados
        time = validated_data.pop('time', None)  # Permitir None si no está presente
        label = validated_data.pop('label', None)  # Permitir None si no está presente
        week = validated_data.pop('week', None)  # Permitir None si no está presente
        date = validated_data.pop('date', None)  # Extraer el valor de date
        
        # Crear la instancia de Exception
        exception = Exception.objects.create(
            **validated_data,
            assignment=assignment,
            dish=dish,  # Asegúrate de pasar el valor correcto aquí
            time=time,
            label=label,
            week=week,
            date=date
        )
        
        # Llamar a add_exception() con los IDs necesarios
        add_exception(dish_id=dish.id, label_id=label.id, assignment_id=assignment.id, time_name=time.name, user=user)
        
        return exception
        
    def update(self, instance, validated_data):
        user = validated_data.pop('user', None)
        
        # Actualizar los campos necesarios
        instance.assignment = validated_data.get('assignment', instance.assignment)
        instance.dish = validated_data.get('dish', instance.dish)
        instance.time = validated_data.get('time', instance.time)
        instance.label = validated_data.get('label', instance.label)
        instance.week = validated_data.get('week', instance.week)
        instance.date = validated_data.get('date', instance.date)

        # Guardar la instancia actualizada
        instance.save()

        # Llamar a add_exception() con los IDs necesarios
        edit_exception(dish_id=instance.dish.id, label_id=instance.label.id if instance.label else None, assignment_id=instance.assignment.id, time_name=instance.time.name if instance.time else None, user=user)

        return instance
    
    def to_internal_value(self, data):
        """
        Sobreescribe la validación para asegurarse de que el esquema esté configurado
        antes de resolver cualquier queryset.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de platos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class DishesSerializer(serializers.ModelSerializer):
    
    dishLang = DishesLangSerializer(many=True, read_only=True)
    recipes = RecipeSerializer(many=True, read_only=True)
    assignments = AssignmentSerializer(many=True, read_only=True)
    exceptions = ExceptionSerializer(many=True, read_only=True)

    class Meta:
        model = Dishes
        fields = ['id', 'dish', 'dishLang', 'recipes', 'assignments', 'exceptions']
        
    def create(self, validated_data):
        dish = Dishes.objects.create(**validated_data)
        
        # Crear traducciones
        self.create_translations(dish)
        
        return dish

    def update(self, instance, validated_data):
        instance.dish = validated_data.get('dish', instance.dish)
        instance.save()
        
        # Actualizar traducciones
        # self.update_translations(instance)

        # Ejecutar la solicitud HTTP al actualizar el plato
        # self.send_update_to_external_api(instance)

        return instance

    def create_translations(self, dish):
        auth_key = '5c16caf8-8b42-4789-83b3-25aca76925f7'  # Reemplaza con tu clave de autenticación
        translator = deepl.Translator(auth_key)
        
        # Filtra los idiomas activos en la base de datos
        active_languages = Language.objects.filter(status=True)

        # Lista para almacenar las instancias de DishesLang
        dishes_lang_instances = []

        # Realiza las traducciones
        for l in active_languages:
            dishTranslate = translator.translate_text(dish.dish, target_lang=l.code)
            print(f"Code: {l.code} Plato a traducir: {dish.dish} Traducción: {dishTranslate.text}")
            
            # Crea una instancia de DishesLang para cada traducción
            dishes_lang_instances.append(DishesLang(dish=dish, language=l.code, translation=dishTranslate.text.upper()))

        # Inserta todas las traducciones en una sola operación
        DishesLang.objects.bulk_create(dishes_lang_instances)

    def update_translations(self, instance):
        auth_key = '5c16caf8-8b42-4789-83b3-25aca76925f7'  # Reemplaza con tu clave de autenticación
        translator = deepl.Translator(auth_key)

        # Filtra las traducciones existentes
        search = DishesLang.objects.filter(dish_id=instance.id)

        # Crea un diccionario para almacenar las traducciones
        translations = {}

        # Realiza las traducciones
        for s in search:
            if s.language not in translations:  # Solo traduce si no se ha traducido antes
                dishTranslate = translator.translate_text(instance.dish, target_lang=s.language)
                translations[s.language] = dishTranslate.text.upper()
                print(f"ID: {instance.id} Code: {s.language} Plato a traducir: {instance.dish} Traducción: {dishTranslate.text}")

        # Actualiza las traducciones en la base de datos
        for s in search:
            if s.language in translations:
                s.translation = translations[s.language]

        # Guarda todos los cambios en una sola operación
        DishesLang.objects.bulk_update(search, ['translation'])
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos los serializadores para editar traducciones de los platos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class DishesLangReferenceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Dishes
        fields = ['id','dish']

class DishesLangEditSerializer(serializers.ModelSerializer):
    
    dish_name = DishesLangReferenceSerializer(source='dish', read_only=True)
    class Meta:
        model = DishesLang
        fields = ['dish_name', 'id', 'dish', 'language', 'translation']
        
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos los serializadores para editar traducciones de los alergenos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AllergenLangReferenceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Allergens
        fields = ['id','allergen']

class AllergenLangEditSerializer(serializers.ModelSerializer):
    
    allergen_name = AllergenLangReferenceSerializer(source='allergen', read_only=True)
    class Meta:
        model = AllergensLang
        fields = ['allergen_name', 'id', 'allergen', 'language', 'translation']
        
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador de dishes alternativo con id y plato
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class OnlyDishesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        fields = ['id', 'dish']
        
