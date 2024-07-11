from django.db import models

class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Label(models.Model):
    mac = models.CharField(max_length=255)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.label