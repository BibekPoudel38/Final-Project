from django.contrib import admin
from .models import InventorModel, SupplierModel

# Register your models here.


admin.site.register(InventorModel)
admin.site.register(SupplierModel)
