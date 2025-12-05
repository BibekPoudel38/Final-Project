import pytest
from media_gen.models import MediaGeneration
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestMediaGenModels:
    def test_media_generation_creation(self):
        user = User.objects.create_user(username="mediauser", password="password")
        media = MediaGeneration.objects.create(
            user=user, prompt="A beautiful sunset", media_type="image"
        )
        assert media.prompt == "A beautiful sunset"
        assert media.media_type == "image"
        assert media.user == user
