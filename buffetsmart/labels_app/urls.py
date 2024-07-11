from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, LabelViewSet

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet)
router.register(r'labels', LabelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]