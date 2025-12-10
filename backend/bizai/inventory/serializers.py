from rest_framework import serializers
from .models import InventorModel


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorModel
        fields = "__all__"
        read_only_fields = [
            "user",
            "business",
            "created_at",
            "updated_at",
            "id",
        ]
