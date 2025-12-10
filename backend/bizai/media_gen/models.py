from django.db import models
from django.conf import settings


class MediaGeneration(models.Model):
    MEDIA_TYPES = (
        ("image", "Image"),
        ("video", "Video"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.TextField()
    original_data = models.JSONField(default=dict)
    input_image = models.ImageField(
        upload_to="media_gen/inputs/", null=True, blank=True
    )
    generated_file = models.FileField(upload_to="media_gen/outputs/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default="image")
    caption = models.TextField(blank=True, null=True)
    hashtags = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} generation by {self.user} at {self.created_at}"


class PromptTemplate(models.Model):
    prompt = models.TextField()
    category = models.CharField(max_length=100, default="General")
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    usage_count = models.IntegerField(default=0)
    original_data = models.JSONField(default=dict)

    def __str__(self):
        return f"Template: {self.prompt[:50]}..."
