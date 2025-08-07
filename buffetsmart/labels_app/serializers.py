from rest_framework import serializers
from .models import Restaurant, Label, Template
from dishes.schema import set_schema
from dishes.utils import schema_context
from dishes.utils import update_labels

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador para restauranes
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador para labels
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = '__all__'
        
    def to_internal_value(self, data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Configura el esquema aquí
            set_schema(request.user)

        return super().to_internal_value(data)
    
    def update(self, instance, validated_data):
        # Aquí puedes saber que es un update
        print("Actualizando la instancia:", instance)
        
        request = self.context.get('request')
        
        # Actualiza los campos de la instancia
        instance.label = validated_data.get('label', instance.label)
        instance.mac = validated_data.get('mac', instance.mac)
        instance.model = validated_data.get('model', instance.model)
        instance.enabled = validated_data.get('enabled', instance.enabled)
        instance.restaurant = validated_data.get('restaurant', instance.restaurant)
        instance.template = validated_data.get('template', instance.template)
        
        print(instance.label, instance.mac, instance.model)
        
        # Llamar a la función de utilidades con los parámetros obtenidos
        update_labels(request.user, instance.label, instance.mac)
        
        instance.save()
        return instance
        
    def validate(self, data):
        # Verificar si enabled es True y restaurant es None
        if data.get('enabled') and data.get('restaurant') is None:
            raise serializers.ValidationError({
                'enabled': 'No puedes habilitar esta etiqueta sin seleccionar un restaurante.'
            })
        return data
        
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Creamos el serializador para templates
# --------------------------------------------------------------------------------------------------------------------------------------------------------------

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'

