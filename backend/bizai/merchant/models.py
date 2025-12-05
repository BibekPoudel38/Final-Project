from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AddressModel(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}, {self.country}"


class BusinessProfileModel(models.Model):
    business_name = models.CharField(max_length=255)
    business_email = models.EmailField(unique=True)
    business_phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.ForeignKey(AddressModel, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # Frontend onboarding fields
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)
    google_maps_link = models.URLField(blank=True, null=True)
    yelp_link = models.URLField(blank=True, null=True)
    clover_connected = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name

    def is_owner(self, user):
        return self.owner == user


class SocialMediaProfileModel(models.Model):
    bizness = models.ForeignKey(BusinessProfileModel, on_delete=models.CASCADE)
    platform = models.CharField(max_length=100)
    profile_url = models.URLField()
    active = models.BooleanField(default=True)
    can_be_used_for_marketing = models.BooleanField(default=False)
    media_type = models.CharField(max_length=50, default="image")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.platform} - {self.profile_url}"

    def is_owned_by(self, business_profile):
        return self.bizness == business_profile
