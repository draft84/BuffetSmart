from django.db import models

# Importamos los modelos de labels_app
from labels_app.models import Label

class Organization(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Role(models.Model):
    can_delete = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_modify = models.BooleanField(default=False)

class User(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return self.username

class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Allergen(models.Model):
    name = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='allergens/')  # Cambiado a ImageField

    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    dish = models.ForeignKey(Dish, related_name='recipes', on_delete=models.CASCADE)
    allergens = models.ManyToManyField(Allergen, related_name='recipes')

    def __str__(self):
        return f"Recipe for {self.dish.name}"

class DishTranslation(models.Model):
    dish = models.ForeignKey(Dish, related_name='translations', on_delete=models.CASCADE)
    language = models.ForeignKey(Language, related_name='dish_translations', on_delete=models.CASCADE)
    translated_name = models.CharField(max_length=100)

class AllergenTranslation(models.Model):
    allergen = models.ForeignKey(Allergen, related_name='translations', on_delete=models.CASCADE)
    language = models.ForeignKey(Language, related_name='allergen_translations', on_delete=models.CASCADE)
    translated_name = models.CharField(max_length=100)
    
class Time(models.Model):
    start = models.TimeField()
    end = models.TimeField()
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Week(models.Model):
    week_num = models.IntegerField()
    week_days = models.IntegerField()
    start_date = models.DateField()

    def __str__(self):
        return f"Week {self.week_num}"

class Assignment(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='assignments')
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
    time = models.ForeignKey(Time, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()

    def __str__(self):
        return f"Assignment for {self.dish} on week {self.week.week_num}, labels {self.label.label} day {self.day_of_week} at {self.time}"
    
class Exception(models.Model):
    dish = models.ForeignKey(Dish, related_name='exceptions', on_delete=models.CASCADE)
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    time = models.ForeignKey(Time, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    date = models.DateField()
    