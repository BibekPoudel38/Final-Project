import pytest
from merchant.models import BusinessProfileModel, AddressModel, UserProfileModel
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestMerchantModels:
    def test_business_profile_creation(self):
        user = User.objects.create_user(username="merchantuser", password="password")
        address = AddressModel.objects.create(
            street="123 Merchant St",
            city="Merchant City",
            state="Merchant State",
            zip_code="12345",
            country="Merchant Country",
        )
        business = BusinessProfileModel.objects.create(
            user=user,
            business_name="Test Business",
            business_address=address,
            business_type="Retail",
            owner=user,
            address=address,
        )
        assert business.business_name == "Test Business"
        assert business.owner == user

    def test_user_profile_creation(self):
        user = User.objects.create_user(username="profileuser", password="password")
        profile = UserProfileModel.objects.create(
            name="Test User", email="test@profile.com", auth_id=user, user_type="Owner"
        )
        assert profile.name == "Test User"
        assert profile.auth_id == user
