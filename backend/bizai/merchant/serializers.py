from rest_framework import serializers
from .models import UserProfileModel, AddressModel, BusinessProfileModel, SocialMediaProfileModel

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileModel
        fields = ['name', 'email', 'phone_number', 'user_type']
        read_only_fields = ['auth_id', 'email']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressModel
        fields = ['street', 'city', 'state', 'zip_code', 'country']

class SocialMediaProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaProfileModel
        fields = ['platform', 'profile_url', 'active', 'can_be_used_for_marketing', 'media_type']

class BusinessProfileSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = BusinessProfileModel
        fields = [
            'business_name', 'business_email', 'business_phone',
            'address', 'google_maps_link', 'yelp_link',
            'website', 'industry', 'description', 'established_date'
        ]

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = AddressModel.objects.create(**address_data)
        # Owner should be provided via serializer context
        owner = self.context.get('owner')
        business_profile = BusinessProfileModel.objects.create(address=address, owner=owner, **validated_data)
        return business_profile