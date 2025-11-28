from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from django.shortcuts import get_object_or_404


class ChatHistoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        session, created = ChatSession.objects.get_or_create(session_id=session_id)
        # If user is authenticated, link them
        if request.user.is_authenticated and not session.user:
            session.user = request.user
            session.save()

        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)

    def post(self, request, session_id):
        session, created = ChatSession.objects.get_or_create(session_id=session_id)
        if request.user.is_authenticated and not session.user:
            session.user = request.user
            session.save()

        data = request.data

        # If data is a list (batch insert), handle it
        if isinstance(data, list):
            for item in data:
                item["session"] = session.id
            serializer = ChatMessageSerializer(data=data, many=True)
        else:
            data["session"] = session.id
            serializer = ChatMessageSerializer(data=data)

        if serializer.is_valid():
            serializer.save(session=session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClearChatView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id)
        session.messages.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
