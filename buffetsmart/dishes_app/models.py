from django.db import models
from rest_framework.pagination import PageNumberPagination

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Importamos los modelos de labels_app
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
from labels.models import Label, Restaurant

class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 9999999999999999999

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------- CREAR IDIOMAS ROLES Y USUARIOS ---------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de organizacion
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Organization(models.Model):
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=10)
    store_code = models.CharField(max_length=20)

    def __str__(self):
        return self.name

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de role
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Role(models.Model):
    limited = models.BooleanField(default=False)
    corporated = models.BooleanField(default=False)
    advanced = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Permisos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Permission(models.Model):
    permissions = models.CharField(max_length=255, unique=True)
    limited = models.BooleanField(default=False)
    corporated = models.BooleanField(default=False)
    advanced = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    def __str__(self):
        return self.permissions

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de usuarios
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class UserApp(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    schema = models.CharField(max_length=255)
    
    def __str__(self):
        return self.username

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de idiomas
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Language(models.Model):
    code = models.CharField(max_length=5)
    name = models.CharField(max_length=30)
    status = models.BooleanField(default=False)
    position = models.IntegerField()

    def __str__(self):
        return self.code

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------- PLATOS RECIPES Y ALEERGENOS -----------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
     
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de platos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Dishes(models.Model):
    dish = models.TextField()
    synchronized = models.BooleanField(default=False)
    
    def __str__(self):
        return self.dish
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de los platos en los idiomas deseados
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class DishesLang(models.Model):
    dish = models.ForeignKey(Dishes, related_name='dishLang', on_delete=models.CASCADE)
    language = models.CharField(max_length=100)
    translation = models.TextField()
    
    def __str__(self):
        # Retornamos los valores necesarios
        return f'Language: {self.language}, Translation: {self.translation}'

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de alergenos
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Allergens(models.Model):
    allergen = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='allergens/', blank=True, null=True)

    def __str__(self):
        return self.allergen

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de los alergenos en los idiomas deseados
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class AllergensLang(models.Model):
    allergen = models.ForeignKey(Allergens, related_name='allergenLang', on_delete=models.CASCADE)
    language = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    
    def __str__(self):
        # Retornamos los valores necesarios
        return f'Language: {self.language}, Translation: {self.translation}'

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de recipes
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Recipe(models.Model):
    dish = models.ForeignKey(Dishes, related_name='recipes', on_delete=models.CASCADE)
    allergens = models.ManyToManyField(Allergens, related_name='recipes')

    def __str__(self):
        return f"Recipe for {self.dish}"

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------- ASIGNACION DE DISPONIBLILIDAD PARA LOS PLATOS --------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de horarios
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Time(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    start = models.TimeField()
    end = models.TimeField()
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de semanas
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Week(models.Model):
    name = models.CharField(max_length=100)
    week_num = models.IntegerField()
    week_days = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"Week {self.week_num}"
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de asignaciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Assignment(models.Model):
    dish = models.ForeignKey(Dishes, on_delete=models.CASCADE, related_name='assignments')
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
    time = models.ForeignKey(Time, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()

    def __str__(self):
        return f"Assignment for {self.dish}, name {self.week.name}, on week {self.week.week_num}, on week {self.week.week_num}, labels {self.label.label} day {self.day_of_week} at {self.time}"

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Menu Management ----------------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class MenuManagement (models.Model):
    dish = models.ForeignKey(Dishes, on_delete=models.CASCADE, related_name='menumanagement')
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
    time = models.ForeignKey(Time, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()

    def __str__(self):
        return f"Menu Management for {self.dish}, name {self.week.name}, on week {self.week.week_num}, on week {self.week.week_num}, labels {self.label.label} day {self.day_of_week} at {self.time}"

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos la tabla de excepciones
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Exception(models.Model):
    dish = models.ForeignKey(Dishes, related_name='exceptions', on_delete=models.CASCADE)
    week = models.ForeignKey(Week, on_delete=models.CASCADE)
    time = models.ForeignKey(Time, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    date = models.DateField()

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Tabla de registros de reuedas y excepciones realizadas
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class DayliMenu(models.Model):
    date = models.DateField(auto_now_add=True)
    hour = models.TimeField(auto_now=True)
    assignments = models.IntegerField()
    turn = models.CharField(max_length=100)
    hour_start = models.CharField(max_length=10)
    hour_end = models.CharField(max_length=10)
    exception = models.IntegerField()
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Log de informacion y errores de ejecucion
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
class Logs(models.Model):
    date = models.DateField(auto_now_add=True)
    hour = models.TimeField(auto_now=True)
    function = models.CharField(max_length=60)
    description = models.TextField()
    status = models.CharField(max_length=20)


# from django.db import models
# from rest_framework.pagination import PageNumberPagination

# -------------------------------------------------------------------
# Importamos los modelos de labels_app
# -------------------------------------------------------------------
# from labels.models import Label, Restaurant

# class Pagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 9999999999999999999

# -------------------------------------------------------------------
# CREAR IDIOMAS ROLES Y USUARIOS
# -------------------------------------------------------------------

# class Organization(models.Model):
#     name = models.CharField(max_length=255)
#     company = models.CharField(max_length=10)
#     store_code = models.CharField(max_length=20)

#     def __str__(self):
#         return self.name

#     class Meta:
#         managed = False
#         db_table = 'dishes_organization'


# class Role(models.Model):
#     limited = models.BooleanField(default=False)
#     corporated = models.BooleanField(default=False)
#     advanced = models.BooleanField(default=False)
#     admin = models.BooleanField(default=False)

#     class Meta:
#         managed = False
#         db_table = 'dishes_role'


# class Permission(models.Model):
#     permissions = models.CharField(max_length=255, unique=True)
#     limited = models.BooleanField(default=False)
#     corporated = models.BooleanField(default=False)
#     advanced = models.BooleanField(default=False)
#     admin = models.BooleanField(default=False)

#     def __str__(self):
#         return self.permissions

#     class Meta:
#         managed = False
#         db_table = 'dishes_permission'


# class UserApp(models.Model):
#     role = models.ForeignKey(Role, on_delete=models.CASCADE)
#     organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
#     username = models.CharField(max_length=255, unique=True)
#     password = models.CharField(max_length=255)
#     full_name = models.CharField(max_length=255)
#     enabled = models.BooleanField(default=True)
#     schema = models.CharField(max_length=255)
    
#     def __str__(self):
#         return self.username

#     class Meta:
#         managed = False
#         db_table = 'dishes_userapp'


# class Language(models.Model):
#     code = models.CharField(max_length=5)
#     name = models.CharField(max_length=30)
#     status = models.BooleanField(default=False)
#     position = models.IntegerField()

#     def __str__(self):
#         return self.code

#     class Meta:
#         managed = False
#         db_table = 'dishes_language'


# -------------------------------------------------------------------
# PLATOS, RECIPES Y ALERGENOS
# -------------------------------------------------------------------

# class Dishes(models.Model):
#     dish = models.TextField()
#     synchronized = models.BooleanField(default=False)
    
#     def __str__(self):
#         return self.dish
    
#     class Meta:
#         managed = False
#         db_table = 'dishes_dishes'


# class DishesLang(models.Model):
#     dish = models.ForeignKey(Dishes, related_name='dishLang', on_delete=models.CASCADE)
#     language = models.CharField(max_length=100)
#     translation = models.TextField()
    
#     def __str__(self):
#         return f'Language: {self.language}, Translation: {self.translation}'

#     class Meta:
#         managed = False
#         db_table = 'dishes_disheslang'


# class Allergens(models.Model):
#     allergen = models.CharField(max_length=100)
#     picture = models.ImageField(upload_to='allergens/', blank=True, null=True)

#     def __str__(self):
#         return self.allergen

#     class Meta:
#         managed = False
#         db_table = 'dishes_allergens'


# class AllergensLang(models.Model):
#     allergen = models.ForeignKey(Allergens, related_name='allergenLang', on_delete=models.CASCADE)
#     language = models.CharField(max_length=100)
#     translation = models.CharField(max_length=100)
    
#     def __str__(self):
#         return f'Language: {self.language}, Translation: {self.translation}'

#     class Meta:
#         managed = False
#         db_table = 'dishes_allergenslang'


# class Recipe(models.Model):
#     dish = models.ForeignKey(Dishes, related_name='recipes', on_delete=models.CASCADE)
#     allergens = models.ManyToManyField(Allergens, related_name='recipes')

#     def __str__(self):
#         return f"Recipe for {self.dish}"

#     class Meta:
#         managed = False
#         db_table = 'dishes_recipe'


# -------------------------------------------------------------------
# ASIGNACIÓN DE DISPONIBILIDAD PARA LOS PLATOS
# -------------------------------------------------------------------

# class Time(models.Model):
#     restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
#     start = models.TimeField()
#     end = models.TimeField()
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name

#     class Meta:
#         managed = False
#         db_table = 'dishes_time'


# class Week(models.Model):
#     name = models.CharField(max_length=100)
#     week_num = models.IntegerField()
#     week_days = models.IntegerField()
#     start_date = models.DateField()
#     end_date = models.DateField()
#     restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
#     active = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Week {self.week_num}"

#     class Meta:
#         managed = False
#         db_table = 'dishes_week'


# class Assignment(models.Model):
#     dish = models.ForeignKey(Dishes, on_delete=models.CASCADE, related_name='assignments')
#     week = models.ForeignKey(Week, on_delete=models.CASCADE)
#     label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
#     time = models.ForeignKey(Time, on_delete=models.CASCADE)
#     day_of_week = models.IntegerField()

#     def __str__(self):
#         return (
#             f"Assignment for {self.dish}, week {self.week.week_num} "
#             f"(\"{self.week.name}\"), label {self.label and self.label.label}, "
#             f"day {self.day_of_week} at {self.time}"
#         )

#     class Meta:
#         managed = False
#         db_table = 'dishes_assignment'


# class MenuManagement(models.Model):
#     dish = models.ForeignKey(Dishes, on_delete=models.CASCADE, related_name='menumanagement')
#     week = models.ForeignKey(Week, on_delete=models.CASCADE)
#     label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
#     time = models.ForeignKey(Time, on_delete=models.CASCADE)
#     day_of_week = models.IntegerField()

#     def __str__(self):
#         return (
#             f"MenuManagement for {self.dish}, week {self.week.week_num} "
#             f"(\"{self.week.name}\"), label {self.label and self.label.label}, "
#             f"day {self.day_of_week} at {self.time}"
#         )

#     class Meta:
#         managed = False
#         db_table = 'dishes_menumanagement'


# class Exception(models.Model):
#     dish = models.ForeignKey(Dishes, related_name='exceptions', on_delete=models.CASCADE)
#     week = models.ForeignKey(Week, on_delete=models.CASCADE)
#     time = models.ForeignKey(Time, on_delete=models.CASCADE)
#     label = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
#     assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
#     date = models.DateField()

#     class Meta:
#         managed = False
#         db_table = 'dishes_exception'


# class DayliMenu(models.Model):
#     date = models.DateField(auto_now_add=True)
#     hour = models.TimeField(auto_now=True)
#     assignments = models.IntegerField()
#     turn = models.CharField(max_length=100)
#     hour_start = models.CharField(max_length=10)
#     hour_end = models.CharField(max_length=10)
#     exception = models.IntegerField()

#     class Meta:
#         managed = False
#         db_table = 'dishes_daylimenu'


# class Logs(models.Model):
#     date = models.DateField(auto_now_add=True)
#     hour = models.TimeField(auto_now=True)
#     function = models.CharField(max_length=60)
#     description = models.TextField()
#     status = models.CharField(max_length=20)

#     class Meta:
#         managed = False
#         db_table = 'dishes_logs'
