from django.db import models
from inventory.models import InventorModel


class SalesHolidayModel(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} on {self.date}"


# Create your models here.
class SalesModel(models.Model):
    id = models.AutoField(primary_key=True)
    sales_uid = models.CharField(max_length=100, unique=True)
    prod_id = models.ForeignKey(InventorModel, on_delete=models.CASCADE)
    sale_date = models.DateField()
    quantity_sold = models.DecimalField(max_digits=10, decimal_places=2)
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    customer_flow = models.IntegerField()
    weather_temperature = models.DecimalField(max_digits=5, decimal_places=2)
    weather_condition = models.CharField(max_length=100)
    holidays = models.ManyToManyField(SalesHolidayModel, blank=True)
    was_on_sale = models.BooleanField(default=False)
    promotion_type = models.CharField(max_length=100, null=True, blank=True)
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    flow_students = models.IntegerField(null=True, blank=True)
    flow_family = models.IntegerField(null=True, blank=True)
    flow_adults = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Sales {self.sales_uid} - Product {self.prod_id}"


from django.conf import settings


class TrainingMetrics(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )  # Link to User
    accuracy = models.FloatField()
    loss = models.FloatField()
    mae = models.FloatField(null=True, blank=True)
    mse = models.FloatField(null=True, blank=True)
    rmse = models.FloatField(null=True, blank=True)
    mape = models.FloatField(null=True, blank=True)
    r2_score = models.FloatField(null=True, blank=True)
    explained_variance = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=100)
    training_info = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Model {self.model_version} - Acc: {self.accuracy}"
