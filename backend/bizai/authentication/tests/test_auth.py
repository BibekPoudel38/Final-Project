import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthentication:
    def test_create_user(self):
        user = User.objects.create_user(email="test@example.com", password="password")
        assert user.email == "test@example.com"
        assert user.check_password("password")
        assert user.is_active
        assert not user.is_admin

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        assert admin.email == "admin@example.com"
        assert admin.is_admin
        assert admin.is_staff
        assert admin.is_superuser

    def test_create_user_no_email(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email=None, password="password")
