from rest_framework import views, permissions
from .serializers import LoginSerializer, SignupSerializer, ProfileSerializer
from django.contrib.auth import login
from rest_framework.response import Response
from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
    CreateAPIView,
    UpdateAPIView,
)
from rest_framework.mixins import CreateModelMixin
from rest_framework import status
from .models import User
from rest_framework.permissions import IsAuthenticated
import random

# views.py
from rest_framework.views import APIView
import requests
from django.views.decorators.csrf import csrf_exempt

# import email_handler as emailHandler
# from base.permissions import IsVerifiedUser
from rest_framework.decorators import api_view

# Create your views here.


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, format=None):
        """Expect a Supabase `access_token` from the client. Validate it
        with Supabase and create/return a local user record. Django will not
        issue tokens anymore — Supabase is the authority.
        """
        token = request.data.get("access_token") or request.data.get("supabase_token")
        if not token:
            return Response({"error": "access_token (supabase) is required"}, status=status.HTTP_400_BAD_REQUEST)

        # validate token with Supabase
        from .supabase_auth import SupabaseAuthentication

        auth = SupabaseAuthentication()
        user_data = auth.verify_supabase_token(token)
        if not user_data:
            return Response({"error": "Invalid Supabase token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Ensure local user exists
        email = user_data.get("email")
        if not email:
            return Response({"error": "Supabase user has no email"}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create(email=email, is_active=True)

        return Response({"status": True, "message": "Logged in via Supabase", "email": email}, status=status.HTTP_200_OK)


class SignupView(GenericAPIView, CreateModelMixin):
    serializer_class = SignupSerializer
    def post(self, requset, **kwargs):
        """Expect a Supabase `access_token` after the client signs up with
        Supabase. Validate token and create a local user record.
        """
        token = requset.data.get("access_token") or requset.data.get("supabase_token")
        if not token:
            return Response({"error": "access_token (supabase) is required"}, status=status.HTTP_400_BAD_REQUEST)

        from .supabase_auth import SupabaseAuthentication
        auth = SupabaseAuthentication()
        user_data = auth.verify_supabase_token(token)
        if not user_data:
            return Response({"error": "Invalid Supabase token"}, status=status.HTTP_401_UNAUTHORIZED)

        email = user_data.get("email")
        if not email:
            return Response({"error": "Supabase user has no email"}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(email=email, defaults={"is_active": True})
        if created:
            return Response({"status": True, "message": "Account created via Supabase", "email": email}, status=status.HTTP_201_CREATED)
        else:
            return Response({"status": True, "message": "Account already exists", "email": email}, status=status.HTTP_200_OK)


class ProfileView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user, context={"request": request})
        return Response(
            {
                "profile": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ProfileUpdateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(data)
        serializer = ProfileSerializer(data=data, instance=user)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": True,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "status": False,
                    "error": serializer.errors,
                }
            )


class ChangePassword(CreateAPIView):
    permission_classes = [IsAuthenticated]
    

    def create(self, request, *args, **kwargs):
        """Change password via Supabase for authenticated users.

        Expect `access_token` and `new_password` in the request body. This
        will PATCH Supabase's `/auth/v1/user` endpoint.
        """
        access_token = request.data.get("access_token")
        new_password = request.data.get("new_password")
        if not access_token or not new_password:
            return Response({"status": False, "message": "access_token and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)

        from django.conf import settings
        supabase_url = getattr(settings, "SUPABASE_ISSUER", None) or getattr(settings, "SUPABASE_URL", None)
        supabase_key = getattr(settings, "SUPABASE_PUBLIC_KEY", None)
        if not supabase_url or not supabase_key:
            return Response({"status": False, "message": "Supabase configuration missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            resp = requests.patch(
                f"{supabase_url.rstrip('/')}/auth/v1/user",
                json={"password": new_password},
                headers={"Authorization": f"Bearer {access_token}", "apikey": supabase_key, "Content-Type": "application/json"},
                timeout=5,
            )
            if resp.status_code == 200:
                return Response({"status": True, "message": "Password updated in Supabase"}, status=status.HTTP_200_OK)
            return Response({"status": False, "message": resp.text}, status=resp.status_code)
        except requests.RequestException as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# When the user asks for reset password, send the email with the OTP Code to reset the password
@api_view(["POST"])
def send_reset_password_otp(request):
    """Proxy password recovery to Supabase: client calls this endpoint with
    `email` and Supabase will send the recovery email. This replaces the
    local OTP workflow.
    """
    email = request.data.get("email")
    if not email:
        return Response({"status": False, "message": "email is required"}, status=status.HTTP_400_BAD_REQUEST)

    from django.conf import settings
    supabase_url = getattr(settings, "SUPABASE_ISSUER", None) or getattr(settings, "SUPABASE_URL", None)
    supabase_key = getattr(settings, "SUPABASE_PUBLIC_KEY", None)
    if not supabase_url or not supabase_key:
        return Response({"status": False, "message": "Supabase configuration missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        resp = requests.post(
            f"{supabase_url.rstrip('/')}/auth/v1/recover",
            json={"email": email},
            headers={"apikey": supabase_key},
            timeout=5,
        )
        if resp.status_code in (200, 204):
            return Response({"status": True, "message": "Recovery email sent by Supabase"}, status=status.HTTP_200_OK)
        return Response({"status": False, "message": resp.text}, status=resp.status_code)
    except requests.RequestException as e:
        return Response({"status": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Now when the user sends the otp code, check if the otp is correct
# cors exception
@csrf_exempt
@api_view(["POST"])
def verify_reset_password_otp(request):
    return Response({"status": False, "message": "OTP verification is handled by Supabase; use the recovery flow."}, status=status.HTTP_400_BAD_REQUEST)


# Now when the user sends the new password, check if the otp is correct and update the password
@csrf_exempt
@api_view(["POST"])
def reset_password(request):
    """If the client has an authenticated Supabase access token, allow the
    user to change their password by PATCHing Supabase's /auth/v1/user.
    """
    access_token = request.data.get("access_token")
    password = request.data.get("password")
    if not access_token or not password:
        return Response({"status": False, "message": "access_token and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    from django.conf import settings
    supabase_url = getattr(settings, "SUPABASE_ISSUER", None) or getattr(settings, "SUPABASE_URL", None)
    supabase_key = getattr(settings, "SUPABASE_PUBLIC_KEY", None)
    if not supabase_url or not supabase_key:
        return Response({"status": False, "message": "Supabase configuration missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        resp = requests.patch(
            f"{supabase_url.rstrip('/')}/auth/v1/user",
            json={"password": password},
            headers={"Authorization": f"Bearer {access_token}", "apikey": supabase_key, "Content-Type": "application/json"},
            timeout=5,
        )
        if resp.status_code == 200:
            return Response({"status": True, "message": "Password updated in Supabase"}, status=status.HTTP_200_OK)
        return Response({"status": False, "message": resp.text}, status=resp.status_code)
    except requests.RequestException as e:
        return Response({"status": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleLoginAPIView(APIView):

    def post(self, request, format=None):
        print("here")
        id_token = request.data.get("token")

        if id_token is None:
            return Response(
                {"error": "Token missing"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the token
        google_verify_url = (
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        )
        response = requests.get(google_verify_url)
        if response.status_code != 200:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_info = response.json()
        email = user_info["email"]
        name = user_info.get("name", "")

        # Find or create local user. Supabase should be used for issuing tokens
        user, created = User.objects.get_or_create(
            email=email, defaults={"is_active": True}
        )
        return Response({"status": True, "message": "Logged in via Google (client should use Supabase for tokens)", "email": email})
