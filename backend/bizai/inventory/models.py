from django.db import models
from merchant.models import BusinessProfileModel
from django.contrib.auth import get_user_model
from merchant.models import AddressModel


User = get_user_model()
# Create your models here.
class InventorModel(models.Model):
    id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="inventory_images/", null=True, blank=True)
    business = models.ForeignKey(BusinessProfileModel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=255)
    item_description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_unit = models.CharField(max_length=50)
    type = models.CharField(max_length=100)
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    auto_reorder = models.BooleanField(default=False)
    supplier = models.CharField(max_length=255, null=True, blank=True)
    item_location = models.CharField(max_length=255, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_restock_date = models.DateField(null=True, blank=True)
    min_margin_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.item_name
    


class SupplierModel(models.Model):
    id = models.AutoField(primary_key=True)
    contact_person = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    contact_address = models.ForeignKey(AddressModel, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=255)
    supplier_email = models.EmailField()
    supplier_phone = models.CharField(max_length=20)
    

    