import pytest
from inventory.models import InventorModel, SupplierModel
from merchant.models import BusinessProfileModel, AddressModel
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestInventoryModels:
    def test_supplier_creation(self):
        address = AddressModel.objects.create(
            street="123 Supplier St",
            city="Supplier City",
            state="Supplier State",
            zip_code="54321",
            country="Supplier Country",
        )
        supplier = SupplierModel.objects.create(
            contact_person="John Doe",
            contact_email="john@supplier.com",
            contact_phone="1234567890",
            contact_address=address,
            supplier_name="Best Supplier",
            supplier_email="info@supplier.com",
            supplier_phone="0987654321",
        )
        assert supplier.supplier_name == "Best Supplier"
        assert supplier.contact_person == "John Doe"

    def test_inventor_model_creation(self):
        user = User.objects.create_user(username="invuser", password="password")
        address = AddressModel.objects.create(
            street="123 Inv St",
            city="Inv City",
            state="Inv State",
            zip_code="11111",
            country="Inv Country",
        )
        business = BusinessProfileModel.objects.create(
            user=user,
            business_name="Inv Business",
            business_address=address,
            business_type="Retail",
        )
        item = InventorModel.objects.create(
            business=business,
            user=user,
            item_name="Test Item",
            item_description="Test Description",
            quantity=100,
            quantity_unit="pcs",
            type="Test Type",
            min_quantity=10,
            cost_price=50.0,
            selling_price=100.0,
        )
        assert item.item_name == "Test Item"
        assert item.quantity == 100
        assert str(item) == "Test Item"
