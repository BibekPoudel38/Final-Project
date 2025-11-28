from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory
from inventory.views import (
    InventoryDashboardView,
    InventoryCategoryView,
    InventoryListView,
    InventoryExportView,
    InventoryImportView
)
from inventory.models import InventorModel
from merchant.models import BusinessProfileModel, AddressModel
from authentication.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import json

class Command(BaseCommand):
    help = 'Verifies inventory endpoints'

    def handle(self, *args, **options):
        self.stdout.write("Starting Inventory Verification...")
        factory = APIRequestFactory()

        try:
            user = User.objects.first()
            if not user:
                self.stdout.write("No user found. Creating dummy user.")
                user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
            
            business = BusinessProfileModel.objects.first()
            if not business:
                self.stdout.write("No business found. Creating dummy business.")
                address = AddressModel.objects.create(street="123 Test St", city="Test City", state="TS", zip_code="12345", country="Testland")
                business = BusinessProfileModel.objects.create(user=user, business_name="Test Biz", business_address=address)

            # Create dummy inventory items
            self.stdout.write("Creating dummy inventory items...")
            # Check if items exist to avoid duplicates if run multiple times
            if not InventorModel.objects.filter(item_name="Item A").exists():
                InventorModel.objects.create(
                    business=business, user=user, item_name="Item A", quantity=100, cost_price=10, selling_price=20, type="Type1", min_quantity=10
                )
            if not InventorModel.objects.filter(item_name="Item B").exists():
                InventorModel.objects.create(
                    business=business, user=user, item_name="Item B", quantity=5, cost_price=50, selling_price=100, type="Type2", min_quantity=10
                )

            # 1. Test Dashboard
            self.stdout.write("\nTesting Dashboard Endpoint...")
            request = factory.get('/api/inventory/dashboard/')
            view = InventoryDashboardView.as_view()
            response = view(request)
            self.stdout.write(f"Dashboard Status: {response.status_code}")
            self.stdout.write(f"Dashboard Data: {response.data}")
            
            # 2. Test Category Breakdown
            self.stdout.write("\nTesting Category Breakdown Endpoint...")
            request = factory.get('/api/inventory/category-breakdown/')
            view = InventoryCategoryView.as_view()
            response = view(request)
            self.stdout.write(f"Category Status: {response.status_code}")
            self.stdout.write(f"Category Data: {response.data}")

            # 3. Test List
            self.stdout.write("\nTesting List Endpoint...")
            request = factory.get('/api/inventory/list/')
            view = InventoryListView.as_view()
            response = view(request)
            self.stdout.write(f"List Status: {response.status_code}")
            # self.stdout.write(f"List Data: {response.data}")

            # 4. Test Export
            self.stdout.write("\nTesting Export Endpoint...")
            request = factory.get('/api/inventory/export/')
            view = InventoryExportView.as_view()
            response = view(request)
            self.stdout.write(f"Export Status: {response.status_code}")
            self.stdout.write(f"Export Content Type: {response['Content-Type']}")
            content = response.content.decode('utf-8')
            self.stdout.write(f"Export Content Preview: {content[:100]}...")

            # 5. Test Import
            self.stdout.write("\nTesting Import Endpoint...")
            csv_content = "item_name,quantity,cost_price,selling_price,type,min_quantity,business,user\nItem C,20,15,30,Type1,5,1,1"
            file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")
            
            request = factory.post('/api/inventory/import/', {'file': file}, format='multipart')
            view = InventoryImportView.as_view()
            response = view(request)
            self.stdout.write(f"Import Status: {response.status_code}")
            self.stdout.write(f"Import Data: {response.data}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Verification Failed: {e}"))
            import traceback
            traceback.print_exc()
