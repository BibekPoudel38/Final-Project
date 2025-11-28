# your_app/auth_backend.py

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import requests
from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()


def _get_supabase_config():
    # Prefer settings values, fallback to older hardcoded values
    supabase_url = getattr(settings, "SUPABASE_ISSUER", None) or getattr(settings, "SUPABASE_URL", None)
    supabase_key = getattr(settings, "SUPABASE_PUBLIC_KEY", None) or getattr(settings, "SUPABASE_API_KEY", None)
    if supabase_url and supabase_url.endswith("/auth/v1") is False:
        # Ensure we have base URL like https://xyz.supabase.co
        supabase_url = supabase_url.rstrip("/")
    return supabase_url, supabase_key


class SupabaseAuthentication(BaseAuthentication):
    """Authenticate requests using Supabase JWTs and map to local Django users.

    This class verifies the Bearer token with Supabase and then looks up (or
    creates) a local Django `User` by email. This allows the rest of the
    application to operate on Django model users while Supabase handles
    authentication.
    """

    def enforce_csrf(self, request):
        return

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        user_data = self.verify_supabase_token(token)
        if not user_data:
            raise AuthenticationFailed("Invalid or expired Supabase token")

        email = user_data.get("email")
        if not email:
            raise AuthenticationFailed("Supabase user has no email")

        user, created = User.objects.get_or_create(email=email, defaults={"is_active": True})
        return (user, None)

    def verify_supabase_token(self, token):
        supabase_url, supabase_key = _get_supabase_config()
        if not supabase_url or not supabase_key:
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": supabase_key,
        }
        try:
            # Supabase exposes the user endpoint at /auth/v1/user
            resp = requests.get(f"{supabase_url.rstrip('/')}/auth/v1/user", headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except requests.RequestException:
            pass
        return None
