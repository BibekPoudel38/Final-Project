import pytest
import json
from django.contrib.auth import get_user_model
from merchant.models import BusinessProfileModel, AddressModel
from inventory.models import InventorModel, SupplierModel

User = get_user_model()


@pytest.mark.django_db
class TestInventoryGraphQL:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.user = User.objects.create_user(
            username="invgraphqluser", password="password"
        )
        self.address = AddressModel.objects.create(
            street="123 Inv St",
            city="Inv City",
            state="Inv State",
            zip_code="11111",
            country="Inv Country",
        )
        self.business = BusinessProfileModel.objects.create(
            user=self.user,
            business_name="Inv Business",
            business_address=self.address,
            business_type="Retail",
            owner=self.user,
            address=self.address,
        )
        self.item = InventorModel.objects.create(
            business=self.business,
            user=self.user,
            item_name="Test Item",
            item_description="Test Description",
            quantity=100,
            quantity_unit="pcs",
            type="Test Type",
            min_quantity=10,
            cost_price=50.0,
            selling_price=100.0,
        )
        self.supplier = SupplierModel.objects.create(
            contact_person="John Doe",
            contact_email="john@supplier.com",
            contact_phone="1234567890",
            contact_address=self.address,
            supplier_name="Best Supplier",
            supplier_email="info@supplier.com",
            supplier_phone="0987654321",
        )

    def test_all_inventory_query(self):
        query = """
        query {
            allInventory {
                edges {
                    node {
                        itemName
                        quantity
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
        assert len(content["data"]["allInventory"]["edges"]) == 1
        assert (
            content["data"]["allInventory"]["edges"][0]["node"]["itemName"]
            == "Test Item"
        )

    def test_all_suppliers_query(self):
        query = """
        query {
            allSuppliers {
                edges {
                    node {
                        supplierName
                        contactPerson
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
        assert len(content["data"]["allSuppliers"]["edges"]) == 1
        assert (
            content["data"]["allSuppliers"]["edges"][0]["node"]["supplierName"]
            == "Best Supplier"
        )
