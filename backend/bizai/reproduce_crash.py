import os
import django
import sys
import json
from django.core.files.uploadedfile import SimpleUploadedFile

# Add the current directory to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bizai.settings")
django.setup()

from django.contrib.auth import get_user_model
from merchant.views import OnboardingView
from merchant.models import BusinessProfileModel, UserProfileModel, AddressModel
from rest_framework.test import APIRequestFactory, force_authenticate
from django.test import Client

User = get_user_model()


def reproduce_crash():
    print("Setting up reproduction...", flush=True)

    try:
        user, created = User.objects.get_or_create(email="crash_test@example.com")
    except Exception as e:
        print(f"Error creating user: {e}")
        return

    if created:
        user.set_password("password")
        user.save()
        if not UserProfileModel.objects.filter(auth_id=user).exists():
            UserProfileModel.objects.create(
                auth_id=user, name="Crash Test User", email="crash@test.com"
            )

    # Clean up previous runs
    BusinessProfileModel.objects.filter(owner=user).delete()

    client = Client()

    # Prepare payload
    payload = {
        "userProfile": {
            "name": "Bibek Poudel",
            "phone_number": "15627096087",
            "email": "poudelbibek38@gmail.com",
        },
        "businessProfile": {
            "business_name": "Bibek Poudelk",
            "business_email": "bibek@store.com",
            "business_phone": "15627096087",
            "website": "https://google.com",
            "industry": "retail",
            "description": "https://google.com",
            "established_date": "2002-03-13",
            "google_maps_link": "https://google.com",
            "yelp_link": "https://google.com",
            "address": {
                "street": "11634 183rd st Apt K",
                "city": "ARTESIA",
                "state": "Ca",
                "zip_code": "90701",
                "country": "United States",
            },
        },
        "socialProfiles": [
            {
                "active": True,
                "can_be_used_for_marketing": False,
                "custom_platform": "",
                "media_type": "image",
                "platform": "Instagram",
                "profile_url": "https://google.com",
            }
        ],
    }

    # Create a dummy CSV file
    csv_content = b"Date,Amount\n2024-01-01,100\n2024-01-02,200"
    csv_file = SimpleUploadedFile("sales.csv", csv_content, content_type="text/csv")

    data = {"data": json.dumps(payload), "file": csv_file}

    # User's token from logs
    token = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImhkRGNqVU12aERqdTE1K28iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FzeHNobnJidGZsaXBtdWhpbXRyLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyZmExODlkZC1mMDYwLTQyODgtYmY5NS03ZTBlZjkxNTE3NGUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY0ODE4NjUxLCJpYXQiOjE3NjQ4MTUwNTEsImVtYWlsIjoicG91ZGVsYmliZWszOEBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoicG91ZGVsYmliZWszOEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIyZmExODlkZC1mMDYwLTQyODgtYmY5NS03ZTBlZjkxNTE3NGUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc2MzY1MzQ1MX1dLCJzZXNzaW9uX2lkIjoiZDFjZWI5MzMtMWQ1Yy00YzM2LTg1YjEtZTMyNDhhNWI2ZWE1IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.37uYzN3I1iqG3NdymHgj0uN4xb_bvyyt3ZFcFsAianY"

    print("Sending POST request with Client (Middleware enabled)...", flush=True)

    # Client.post handles multipart automatically if data contains file objects
    try:
        response = client.post(
            "/api/merchant/onboarding/", data, HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.content}")
    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    reproduce_crash()
