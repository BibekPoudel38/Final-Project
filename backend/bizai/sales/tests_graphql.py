import json
from django.test import TestCase, Client
from .models import SalesModel, SalesHolidayModel
from inventory.models import InventorModel
from datetime import date


class SalesGraphQLTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create dummy data
        self.product = InventorModel.objects.create(
            item_name="Test Product", selling_price=10.0, cost_price=5.0, quantity=100
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
            "/graphql/", {"query": query}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertNotIn("errors", content)
        self.assertEqual(len(content["data"]["allSales"]["edges"]), 1)
        self.assertEqual(
            content["data"]["allSales"]["edges"][0]["node"]["salesUid"], "SALE001"
        )
        self.assertEqual(
            content["data"]["allSales"]["edges"][0]["node"]["prodId"]["itemName"],
            "Test Product",
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
            "/graphql/", {"query": query}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content["data"]["allSales"]["edges"]), 1)

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
            "/graphql/", {"query": query_empty}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(len(content["data"]["allSales"]["edges"]), 0)

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
            "/graphql/", {"query": query}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertNotIn("errors", content)
        self.assertEqual(len(content["data"]["allSalesHolidays"]["edges"]), 1)
        self.assertEqual(
            content["data"]["allSalesHolidays"]["edges"][0]["node"]["name"],
            "Test Holiday",
        )
