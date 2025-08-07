from django.db import models
from rest_framework.pagination import PageNumberPagination

class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 9999999999999999999

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de restaurantes
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de templetes
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class Template(models.Model):
    name = models.CharField(max_length=255)
    label_type = models.CharField(max_length=255)
    base_64_image = models.TextField()

    def __str__(self):
        return self.name
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de labels
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class Label(models.Model):
    mac = models.CharField(max_length=255)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    template = models.ForeignKey(Template, on_delete=models.CASCADE, null=True, blank=True)
    model = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.label
