import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bizai.settings")
django.setup()

from django.contrib.auth import get_user_model
from merchant.models import BusinessProfileModel, AddressModel
from inventory.models import InventorModel, SupplierModel


def run():
    print("Starting test...")
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="test_admin", defaults={"email": "test@example.com"}
    )
    print("User created")

    address, _ = AddressModel.objects.get_or_create(
        street="123 Test St",
        city="Test City",
        state="CA",
        zip_code="90000",
        country="USA",
    )
    print("Address created")

    try:
        business, _ = BusinessProfileModel.objects.get_or_create(
            business_name="Test Biz",
            defaults={
                "address": address,
                "business_email": "test@biz.com",
                "owner": user,
            },
        )
        print("Business created")
    except Exception as e:
        print(f"Business creation failed: {e}")

    try:
        supplier, _ = SupplierModel.objects.get_or_create(
            supplier_name="Test Supplier",
            defaults={
                "contact_person": "Test Person",
                "contact_email": "test@supp.com",
                "contact_phone": "123",
                "contact_address": address,
                "supplier_email": "info@supp.com",
                "supplier_phone": "123",
            },
        )
        print("Supplier created")
    except Exception as e:
        print(f"Supplier creation failed: {e}")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        import traceback

        with open("error_log.txt", "w") as f:
            traceback.print_exc(file=f)
