from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LanguageViewSet, UserViewSet, RoleViewSet, OrganizationViewSet, AllergenViewSet, DishViewSet, RecipeViewSet, TimeViewSet, WeekViewSet, AssignmentViewSet, ExceptionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'organizations', OrganizationViewSet)
router.register(r'languages', LanguageViewSet)
router.register(r'allergens', AllergenViewSet)
router.register(r'dishes', DishViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'times', TimeViewSet)
router.register(r'weeks', WeekViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'exceptions', ExceptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
