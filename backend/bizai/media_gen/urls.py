from django.urls import path
from .views import MediaGenerationView, MediaHistoryView

urlpatterns = [
    path("generate/", MediaGenerationView.as_view(), name="media-generate"),
    path("history/", MediaHistoryView.as_view(), name="media-history"),
]
