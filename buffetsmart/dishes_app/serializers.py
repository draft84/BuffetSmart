from rest_framework import serializers
from .models import User, Role, Organization, Language, Allergen, Dish, Recipe, DishTranslation, AllergenTranslation, Time, Week, Assignment, Exception, Label
from googletrans import Translator

# Importamos serializadores de labels_app
from labels_app.serializers import LabelSerializer
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer()
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())

    class Meta:
        model = User
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = RoleSerializer(instance.role).data
        return representation

    def create(self, validated_data):
        role_data = validated_data.pop('role')
        organization = validated_data.pop('organization')

        role, created = Role.objects.get_or_create(**role_data)
        
        user = User.objects.create(role=role, organization=organization, **validated_data)
        return user

    def update(self, instance, validated_data):
        role_data = validated_data.pop('role', None)
        organization = validated_data.pop('organization', None)

        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.enabled = validated_data.get('enabled', instance.enabled)

        if organization:
            instance.organization = organization

        if role_data:
            role, created = Role.objects.get_or_create(**role_data)
            instance.role = role

        instance.save()
        return instance


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'

class AllergenTranslationSerializer(serializers.ModelSerializer):
    language = serializers.StringRelatedField()

    class Meta:
        model = AllergenTranslation
        fields = ('id', 'language', 'translated_name', 'allergen')

class AllergenSerializer(serializers.ModelSerializer):
    translations = AllergenTranslationSerializer(many=True, read_only=True)

    class Meta:
        model = Allergen
        fields = ('id', 'name', 'picture', 'translations')

class DishTranslationSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()
    class Meta:
        model = DishTranslation
        fields = '__all__'

class RecipeSerializer(serializers.ModelSerializer):
    allergens = AllergenSerializer(many=True, read_only=True)
    allergen_ids = serializers.PrimaryKeyRelatedField(queryset=Allergen.objects.all(), many=True, write_only=True, source='allergens')

    class Meta:
        model = Recipe
        fields = ('id', 'allergens', 'dish', 'allergen_ids')

    def create(self, validated_data):
        allergens_data = validated_data.pop('allergens', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.allergens.set(allergens_data)
        return recipe

    def update(self, instance, validated_data):
        allergens_data = validated_data.pop('allergens', [])
        instance = super().update(instance, validated_data)
        instance.allergens.set(allergens_data)
        return instance
    
# class DishSerializer(serializers.ModelSerializer):
#     translations = DishTranslationSerializer(many=True, read_only=True)
#     recipes = RecipeSerializer(many=True, read_only=True)
#     assignments = serializers.SerializerMethodField()

#     class Meta:
#         model = Dish
#         fields = '__all__'

#     def get_assignments(self, obj):
#         assignments = Assignment.objects.filter(dish=obj)
#         return AssignmentSerializer(assignments, many=True).data
        
class TimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Time
        fields = '__all__'

class WeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Week
        fields = '__all__'

class AssignmentSerializer(serializers.ModelSerializer):
    dish = serializers.PrimaryKeyRelatedField(queryset=Dish.objects.all())
    week = serializers.PrimaryKeyRelatedField(queryset=Week.objects.all())
    time = serializers.PrimaryKeyRelatedField(queryset=Time.objects.all())
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all(), required=False, allow_null=True)
    times = serializers.SerializerMethodField()
    labels = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = ('id', 'dish', 'week', 'label', 'time', 'day_of_week', 'times', 'labels')

    def get_times(self, obj):
        times = Time.objects.all()
        return TimeSerializer(times, many=True).data

    def get_labels(self, obj):
        labels = Label.objects.all()
        return LabelSerializer(labels, many=True).data

    def create(self, validated_data):
        return Assignment.objects.create(**validated_data)

class ExceptionSerializer(serializers.ModelSerializer):
    dish = serializers.PrimaryKeyRelatedField(queryset=Dish.objects.all())
    week = serializers.PrimaryKeyRelatedField(queryset=Week.objects.all())
    time = serializers.PrimaryKeyRelatedField(queryset=Time.objects.all())
    assignment = serializers.PrimaryKeyRelatedField(queryset=Assignment.objects.all())
    label = LabelSerializer()

    class Meta:
        model = Exception
        fields = '__all__'
        
class DishSerializer(serializers.ModelSerializer):
    translations = DishTranslationSerializer(many=True, read_only=True)
    recipes = RecipeSerializer(many=True, read_only=True)
    assignments = AssignmentSerializer(many=True, read_only=True)
    exceptions = ExceptionSerializer(many=True, read_only=True)

    class Meta:
        model = Dish
        fields = '__all__'
        
    # Actualizamos el plato y sus traducciones asociadas
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        # Instancia Google Translate
        translator = Translator()
        active_languages = Language.objects.filter(status=True)

        # Actualizamos las el plato en los idiomas correspondientes
        for translation in instance.translations.all():
            language_code = translation.language.code
            translated_name = translator.translate(instance.name, dest=language_code).text
            translation.translated_name = translated_name
            translation.save()

        return instance