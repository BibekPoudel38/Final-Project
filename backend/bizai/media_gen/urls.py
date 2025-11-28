from django.urls import path
from .views import MediaGenerationView

urlpatterns = [
    path("generate/", MediaGenerationView.as_view(), name="media-generate"),
]
