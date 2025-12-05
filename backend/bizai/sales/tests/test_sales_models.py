import pytest
from datetime import date
from sales.models import SalesModel, SalesHolidayModel
from inventory.models import InventorModel
from merchant.models import BusinessProfileModel, AddressModel
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestSalesModels:
    def test_sales_holiday_creation(self):
        holiday = SalesHolidayModel.objects.create(
            name="Christmas", date=date(2023, 12, 25)
        )
        assert holiday.name == "Christmas"
        assert str(holiday) == "Christmas on 2023-12-25"

    def test_sales_model_creation(self):
        user = User.objects.create_user(username="testuser", password="password")
        address = AddressModel.objects.create(
            street="123 Test St",
            city="Test City",
            state="Test State",
            zip_code="12345",
            country="Test Country",
        )
        business = BusinessProfileModel.objects.create(
            user=user,
            business_name="Test Business",
            business_address=address,
            business_type="Retail",
        )
        product = InventorModel.objects.create(
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
        sale = SalesModel.objects.create(
            sales_uid="SALE123",
            prod_id=product,
            sale_date=date(2023, 12, 25),
            quantity_sold=10,
            revenue=1000.0,
            customer_flow=50,
            weather_temperature=20.0,
            weather_condition="Sunny",
        )
        assert sale.sales_uid == "SALE123"
        assert sale.revenue == 1000.0
        assert str(sale) == f"Sales SALE123 - Product {product}"
