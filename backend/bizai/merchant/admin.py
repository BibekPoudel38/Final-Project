from django.contrib import admin
from .models import UserProfileModel, BusinessProfileModel, AddressModel, SocialMediaProfileModel

admin.site.register(UserProfileModel)
admin.site.register(BusinessProfileModel)
admin.site.register(AddressModel)
admin.site.register(SocialMediaProfileModel)