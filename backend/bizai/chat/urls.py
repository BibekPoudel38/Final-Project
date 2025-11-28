from django.urls import path
from .views import ChatHistoryView, ClearChatView

urlpatterns = [
    path("history/<str:session_id>/", ChatHistoryView.as_view(), name="chat-history"),
    path("clear/<str:session_id>/", ClearChatView.as_view(), name="chat-clear"),
]
