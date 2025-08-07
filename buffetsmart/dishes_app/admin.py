from django.contrib import admin
from .models import (
    Organization, Role, UserApp, Language, Dishes, DishesLang,
    Allergens, AllergensLang, Recipe, Time, Week, Assignment, Exception
)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'store_code')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('limited', 'corporated', 'advanced', 'admin')

@admin.register(UserApp)
class UserAppAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'role', 'organization', 'enabled', 'schema')
    search_fields = ('username', 'full_name')

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status')

@admin.register(Dishes)
class DishesAdmin(admin.ModelAdmin):
    list_display = ('dish', 'synchronized')

@admin.register(DishesLang)
class DishesLangAdmin(admin.ModelAdmin):
    list_display = ('dish', 'language', 'translation')

@admin.register(Allergens)
class AllergensAdmin(admin.ModelAdmin):
    list_display = ('allergen', 'picture')

@admin.register(AllergensLang)
class AllergensLangAdmin(admin.ModelAdmin):
    list_display = ('allergen', 'language', 'translation')

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('dish',)
    filter_horizontal = ('allergens',)

@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'start', 'end', 'name')

@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ('name', 'week_num', 'week_days', 'start_date', 'end_date')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('dish', 'week', 'label', 'time', 'day_of_week')

@admin.register(Exception)
class ExceptionAdmin(admin.ModelAdmin):
    list_display = ('dish', 'week', 'time', 'label', 'assignment', 'date')