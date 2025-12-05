import pytest
from chat.models import ChatSession, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestChatModels:
    def test_chat_session_creation(self):
        user = User.objects.create_user(username="chatuser", password="password")
        session = ChatSession.objects.create(user=user, session_id="session123")
        assert session.session_id == "session123"
        assert session.user == user

    def test_chat_message_creation(self):
        user = User.objects.create_user(username="msguser", password="password")
        session = ChatSession.objects.create(user=user, session_id="session456")
        message = ChatMessage.objects.create(
            session=session, role="user", content="Hello AI"
        )
        assert message.content == "Hello AI"
        assert message.role == "user"
        assert message.session == session
