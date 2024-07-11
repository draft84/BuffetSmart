from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Language, User, Role, Organization, Allergen, Dish, Recipe, DishTranslation, AllergenTranslation, Time, Week, Assignment, Exception
from .serializers import LanguageSerializer, UserSerializer, RoleSerializer, OrganizationSerializer, AllergenSerializer, DishSerializer, RecipeSerializer, TimeSerializer, WeekSerializer, AssignmentSerializer, ExceptionSerializer
from googletrans import Translator
from googletrans import LANGUAGES

translator = Translator()

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

class AllergenViewSet(viewsets.ModelViewSet):
    queryset = Allergen.objects.all()
    serializer_class = AllergenSerializer

    def perform_create(self, serializer):
        allergen = serializer.save()
        active_languages = Language.objects.filter(status=True)

        detected_language = None  # Inicialmente no se detecta ningún idioma específico

        try:
            # Detectar el idioma de entrada utilizando googletrans
            detected_lang = translator.detect(allergen.name).lang
            detected_language = LANGUAGES.get(detected_lang, None)  # Obtener el nombre del idioma
            print(f'Detected language for allergen "{allergen.name}": {detected_language}')
        except Exception as e:
            print(f'Failed to detect language for allergen "{allergen.name}": {e}')
            
        COMMON_SPANISH_WORDS = ['leche', 'huevo', 'gluten', 'frutos secos', 'pescado', 'mariscos']
        
        # Verificar si la palabra es una palabra común en español que podría causar problemas
        if allergen.name.lower() in COMMON_SPANISH_WORDS:
            detected_language = 'es'
            print(f'Assuming Spanish for common word: {allergen.name}')

        for language in active_languages:
            if detected_language and detected_language.lower() != language.code.lower():
                translated_name = translator.translate(allergen.name, src=detected_language, dest=language.code).text
                # Agregar registros de depuración
                print(f'Translating allergen "{allergen.name}" to {language.name}: {translated_name}')
                AllergenTranslation.objects.create(allergen=allergen, language=language, translated_name=translated_name)
            else:
                # Si el idioma detectado es igual al idioma de destino, no se traduce
                AllergenTranslation.objects.create(allergen=allergen, language=language, translated_name=allergen.name)

class DishViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer

    def perform_create(self, serializer):
        dish = serializer.save()
        active_languages = Language.objects.filter(status=True)
        for language in active_languages:
            translated_name = translator.translate(dish.name, dest=language.code).text
            DishTranslation.objects.create(dish=dish, language=language, translated_name=translated_name)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe = serializer.save()

        serialized_recipe = RecipeSerializer(recipe)
        return Response(serialized_recipe.data, status=status.HTTP_201_CREATED)

class TimeViewSet(viewsets.ModelViewSet):
    queryset = Time.objects.all()
    serializer_class = TimeSerializer

class WeekViewSet(viewsets.ModelViewSet):
    queryset = Week.objects.all()
    serializer_class = WeekSerializer

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    
class ExceptionViewSet(viewsets.ModelViewSet):
    queryset = Exception.objects.all()
    serializer_class = ExceptionSerializer