import os
import django
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bizai.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from merchant.views import OnboardingView
from merchant.models import BusinessProfileModel, UserProfileModel, AddressModel
from rest_framework.test import APIRequestFactory, force_authenticate

User = get_user_model()


def test_onboarding_view():
    print("Setting up test...", flush=True)

    print("1. Get or create user", flush=True)
    try:
        # Custom User model uses email as identifier
        user, created = User.objects.get_or_create(email="test@example.com")
    except Exception as e:
        print(f"Error 1: {e}")
        raise e

    if created:
        user.set_password("password")
        user.save()
        print("2. Create UserProfile if needed", flush=True)
        try:
            if not UserProfileModel.objects.filter(auth_id=user).exists():
                UserProfileModel.objects.create(auth_id=user, name="Test User")
        except Exception as e:
            print(f"Error 2: {e}")
            raise e

    print("3. Delete BusinessProfile", flush=True)
    try:
        BusinessProfileModel.objects.filter(owner=user).delete()
    except Exception as e:
        print(f"Error 3: {e}")
        raise e

    print("4. Update UserProfile", flush=True)
    try:
        up = UserProfileModel.objects.get(auth_id=user)
        up.business_profile = None
        up.save()
    except Exception as e:
        print(f"Error 4: {e}")
        raise e

    factory = APIRequestFactory()
    request = factory.get("/api/merchant/onboarding/")
    force_authenticate(request, user=user)

    print("\n--- Testing ORM queries directly ---", flush=True)
    try:
        up_test = UserProfileModel.objects.get(auth_id=user)
        print("UserProfileModel query OK")
        bp_test = BusinessProfileModel.objects.filter(owner=user).first()
        print("BusinessProfileModel query OK")
    except Exception as e:
        print(f"ORM Query Failed: {e}")
        raise e

    print("\n--- Testing with no business profile ---", flush=True)
    view = OnboardingView.as_view()
    try:
        response = view(request)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"View Execution Failed: {e}")
        raise e

    if response.status_code != 200:
        print("FAILED: Status code is not 200")
        return

    if response.data["is_complete"] is not False:
        print("FAILED: is_complete should be False")
        return

    print("\n--- Creating incomplete business profile ---", flush=True)
    try:
        # Need to create address first as it is required by BusinessProfileModel
        addr = AddressModel.objects.create(
            street="123 Test St",
            city="Test City",
            state="TS",
            zip_code="12345",
            country="Test Country",
        )

        biz = BusinessProfileModel.objects.create(
            owner=user,
            business_name="Test Biz",
            business_email="biz@test.com",
            business_phone="",  # Empty phone to make it incomplete
            address=addr,
        )
        up.business_profile = biz
        up.save()
    except Exception as e:
        print(f"Error creating business: {e}")
        raise e

    print("Testing with incomplete business profile...", flush=True)
    # Re-create request to be safe or reuse
    request = factory.get("/api/merchant/onboarding/")
    force_authenticate(request, user=user)

    response = view(request)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")

    if response.data["is_complete"] is not False:
        print("FAILED: is_complete should be False for incomplete business")
        return

    if response.data["data"]["businessProfile"]["business_name"] != "Test Biz":
        print("FAILED: Should return existing business data")
        return

    print("\n--- Verification Successful! ---")


if __name__ == "__main__":
    try:
        test_onboarding_view()
    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback

        traceback.print_exc()
