from rest_framework import serializers
from .models import InventorModel

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorModel
        fields = '__all__'
