import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bizai.settings")
django.setup()

from sales.models import SalesModel

count = SalesModel.objects.count()
print(f"Sales count: {count}")
