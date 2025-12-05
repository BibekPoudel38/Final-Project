from django.urls import path
from .views import (
    SalesListView,
    SalesInsightsView,
    TrainModelView,
    TrainingMetricsView,
    ScenarioPredictionView,
    SalesAIChatView,
)

urlpatterns = [
    path("list/", SalesListView.as_view(), name="sales-list"),
    path("insights/", SalesInsightsView.as_view(), name="sales-insights"),
    path("train/", TrainModelView.as_view(), name="sales-train"),
    path("metrics/", TrainingMetricsView.as_view(), name="sales-metrics"),
    path("scenario/", ScenarioPredictionView.as_view(), name="sales-scenario"),
    path("ai_chat/", SalesAIChatView.as_view(), name="sales-ai-chat"),
]
