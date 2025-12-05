from django.contrib import admin
from .models import BusinessProfileModel, AddressModel, SocialMediaProfileModel

admin.site.register(BusinessProfileModel)
admin.site.register(AddressModel)
admin.site.register(SocialMediaProfileModel)
