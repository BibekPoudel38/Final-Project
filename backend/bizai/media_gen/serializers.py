from rest_framework import serializers
from .models import MediaGeneration


class MediaGenerationSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaGeneration
        fields = [
            "id",
            "media_url",
            "prompt",
            "caption",
            "hashtags",
            "media_type",
            "created_at",
        ]

    def get_media_url(self, obj):
        if obj.generated_file:
            return obj.generated_file.url
        return None
