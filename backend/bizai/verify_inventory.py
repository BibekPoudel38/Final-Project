import os
import django
import sys
import json
from io import StringIO

# Setup Django environment
sys.path.append(r'c:\Users\poude\Documents\Final Project\backend\bizai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bizai.settings')
django.setup()

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

def verify_inventory():
    print("Starting Inventory Verification...")
    factory = APIRequestFactory()

    # Create dummy user and business if needed
    # For simplicity, we'll try to fetch existing ones or create simple ones
    # Note: This script assumes DB access.
    
    try:
        user = User.objects.first()
        if not user:
            print("No user found. Creating dummy user.")
            user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        
        business = BusinessProfileModel.objects.first()
        if not business:
            print("No business found. Creating dummy business.")
            # Address is needed for business
            address = AddressModel.objects.create(street="123 Test St", city="Test City", state="TS", zip_code="12345", country="Testland")
            business = BusinessProfileModel.objects.create(user=user, business_name="Test Biz", business_address=address)

        # Create dummy inventory items
        print("Creating dummy inventory items...")
        InventorModel.objects.create(
            business=business, user=user, item_name="Item A", quantity=100, cost_price=10, selling_price=20, type="Type1", min_quantity=10
        )
        InventorModel.objects.create(
            business=business, user=user, item_name="Item B", quantity=5, cost_price=50, selling_price=100, type="Type2", min_quantity=10
        ) # Low stock

        # 1. Test Dashboard
        print("\nTesting Dashboard Endpoint...")
        request = factory.get('/api/inventory/dashboard/')
        view = InventoryDashboardView.as_view()
        response = view(request)
        print(f"Dashboard Status: {response.status_code}")
        print(f"Dashboard Data: {response.data}")
        
        # 2. Test Category Breakdown
        print("\nTesting Category Breakdown Endpoint...")
        request = factory.get('/api/inventory/category-breakdown/')
        view = InventoryCategoryView.as_view()
        response = view(request)
        print(f"Category Status: {response.status_code}")
        print(f"Category Data: {response.data}")

        # 3. Test List
        print("\nTesting List Endpoint...")
        request = factory.get('/api/inventory/list/')
        view = InventoryListView.as_view()
        response = view(request)
        print(f"List Status: {response.status_code}")
        # print(f"List Data: {response.data}") # Might be large

        # 4. Test Export
        print("\nTesting Export Endpoint...")
        request = factory.get('/api/inventory/export/')
        view = InventoryExportView.as_view()
        response = view(request)
        print(f"Export Status: {response.status_code}")
        print(f"Export Content Type: {response['Content-Type']}")
        content = response.content.decode('utf-8')
        print(f"Export Content Preview: {content[:100]}...")

        # 5. Test Import
        print("\nTesting Import Endpoint...")
        csv_content = "item_name,quantity,cost_price,selling_price,type,min_quantity,business,user\nItem C,20,15,30,Type1,5,1,1"
        # Note: business and user IDs might need to be adjusted based on actual IDs
        # But for now let's just see if it parses.
        
        # We need to mock file upload
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")
        
        request = factory.post('/api/inventory/import/', {'file': file}, format='multipart')
        view = InventoryImportView.as_view()
        response = view(request)
        print(f"Import Status: {response.status_code}")
        print(f"Import Data: {response.data}")

    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_inventory()
