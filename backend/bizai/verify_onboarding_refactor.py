import os
import django
import json
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bizai.settings")
django.setup()

from django.contrib.auth import get_user_model
from merchant.models import BusinessProfileModel, SocialMediaProfileModel

User = get_user_model()


def verify_onboarding_flow():
    email = "test_onboarding@example.com"
    password = "password123"

    # 1. Create User
    if User.objects.filter(email=email).exists():
        User.objects.filter(email=email).delete()

    user = User.objects.create_user(email=email, password=password)
    print(
        f"User created: {user.email}, Onboarding Complete: {user.onboarding_complete}"
    )

    # 2. Login (Simulate getting token)
    from rest_framework.test import APIRequestFactory, force_authenticate
    from merchant.views import OnboardingView

    factory = APIRequestFactory()
    view = OnboardingView.as_view()

    # 3. Check Onboarding Status (GET)
    request = factory.get("/api/merchant/onboarding/")
    force_authenticate(request, user=user)
    response = view(request)
    print(f"GET Response: {response.status_code}, Data: {response.data}")
    assert response.data["is_complete"] == False

    # 4. Submit Onboarding Data (POST)
    payload = {
        "userProfile": {
            "name": "Test User",
            "email": email,
            "phone_number": "1234567890",
        },
        "businessProfile": {
            "business_name": "Test Biz",
            "business_email": "biz@example.com",
            "business_phone": "0987654321",
            "website": "https://example.com",
            "industry": "tech",
            "description": "Test Description",
            "established_date": "2023-01-01",
            "google_maps_link": "",
            "yelp_link": "",
            "address": {
                "street": "123 St",
                "city": "City",
                "state": "State",
                "zip_code": "12345",
                "country": "Country",
            },
        },
        "socialProfiles": [
            {
                "platform": "Twitter",
                "profile_url": "https://twitter.com/test",
                "active": True,
                "can_be_used_for_marketing": True,
                "media_type": "both",
            }
        ],
    }

    data = {"data": json.dumps(payload)}

    request = factory.post("/api/merchant/onboarding/", data, format="multipart")
    force_authenticate(request, user=user)
    response = view(request)
    print(f"POST Response: {response.status_code}")
    if response.status_code != 200 and response.status_code != 201:
        print(response.data)

    # 5. Verify Database Updates
    user.refresh_from_db()
    print(f"User Onboarding Complete: {user.onboarding_complete}")
    print(f"User Name: {user.name}")
    print(f"User Phone: {user.phone_number}")

    assert user.onboarding_complete == True
    assert user.name == "Test User"

    biz_profile = user.business_profile
    print(f"Business Profile: {biz_profile.business_name}")
    assert biz_profile.business_name == "Test Biz"

    # FIX: Use 'bizness' instead of 'business_profile'
    social_profiles = SocialMediaProfileModel.objects.filter(bizness=biz_profile)
    print(f"Social Profiles Count: {social_profiles.count()}")
    assert social_profiles.count() == 1


if __name__ == "__main__":
    verify_onboarding_flow()
