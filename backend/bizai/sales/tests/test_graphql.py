import pytest
import json
from datetime import date
from django.contrib.auth import get_user_model
from merchant.models import BusinessProfileModel, AddressModel
from inventory.models import InventorModel
from sales.models import SalesModel, SalesHolidayModel

User = get_user_model()


@pytest.mark.django_db
class TestSalesGraphQL:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.user = User.objects.create_user(username="testuser", password="password")
        self.address = AddressModel.objects.create(
            street="123 Test St",
            city="Test City",
            state="Test State",
            zip_code="12345",
            country="Test Country",
        )
        self.business = BusinessProfileModel.objects.create(
            user=self.user,
            business_name="Test Business",
            business_address=self.address,
            business_type="Retail",
            owner=self.user,
            address=self.address,
        )
        self.product = InventorModel.objects.create(
            business=self.business,
            user=self.user,
            item_name="Test Product",
            item_description="Test Description",
            quantity=100,
            quantity_unit="pcs",
            type="Test Type",
            min_quantity=10,
            cost_price=5.0,
            selling_price=10.0,
        )
        self.holiday = SalesHolidayModel.objects.create(
            name="Test Holiday", date=date(2023, 12, 25)
        )
        self.sale = SalesModel.objects.create(
            sales_uid="SALE001",
            prod_id=self.product,
            sale_date=date(2023, 12, 25),
            quantity_sold=10,
            revenue=100.0,
            customer_flow=50,
            weather_temperature=25.0,
            weather_condition="Sunny",
            was_on_sale=True,
        )
        self.sale.holidays.add(self.holiday)

    def test_all_sales_query(self):
        query = """
        query {
            allSales {
                edges {
                    node {
                        salesUid
                        revenue
                        quantitySold
                        prodId {
                            itemName
                        }
                    }
                }
            }
        }
        """
        response = self.client.post(
            "/graphql/",
            data=json.dumps({"query": query}),
            content_type="application/json",
        )
        assert response.status_code == 200
        content = json.loads(response.content)
        assert "errors" not in content
        assert len(content["data"]["allSales"]["edges"]) == 1
        assert content["data"]["allSales"]["edges"][0]["node"]["salesUid"] == "SALE001"
        assert (
            content["data"]["allSales"]["edges"][0]["node"]["prodId"]["itemName"]
            == "Test Product"
        )

    def test_sales_filter(self):
        query = """
        query {
            allSales(minRevenue: 50) {
                edges {
                    node {
                        salesUid
                    }
                }
            }
        }
        """
        response = self.client.post(
            "/graphql/",
            data=json.dumps({"query": query}),
            content_type="application/json",
        )
        assert response.status_code == 200
        content = json.loads(response.content)
        assert len(content["data"]["allSales"]["edges"]) == 1

        query_empty = """
        query {
            allSales(minRevenue: 200) {
                edges {
                    node {
                        salesUid
                    }
                }
            }
        }
        """
        response = self.client.post(
            "/graphql/",
            data=json.dumps({"query": query_empty}),
            content_type="application/json",
        )
        assert response.status_code == 200
        content = json.loads(response.content)
        assert len(content["data"]["allSales"]["edges"]) == 0

    def test_all_sales_holidays_query(self):
        query = """
        query {
            allSalesHolidays {
                edges {
                    node {
                        name
                        date
                    }
                }
            }
        }
        """
        response = self.client.post(
            "/graphql/",
            data=json.dumps({"query": query}),
            content_type="application/json",
        )
        assert response.status_code == 200
        content = json.loads(response.content)
        assert "errors" not in content
        assert len(content["data"]["allSalesHolidays"]["edges"]) == 1
        assert (
            content["data"]["allSalesHolidays"]["edges"][0]["node"]["name"]
            == "Test Holiday"
        )
