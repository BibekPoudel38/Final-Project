import json
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import (
    BusinessProfileModel,
    SocialMediaProfileModel,
    AddressModel,
)
from .serializers import (
    UserSerializer,
    BusinessProfileSerializer,
    SocialMediaProfileSerializer,
    AddressSerializer,
)

User = get_user_model()


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        """
        Checks if the user (owner or employee) is associated with a complete business profile.
        Returns existing data to pre-fill the form if available.
        """
        try:
            user = request.user

            # Find business: either owned by user or user is an employee of it
            business = None
            if user.business_profile:
                business = user.business_profile
            else:
                business = BusinessProfileModel.objects.filter(
                    owner=request.user
                ).first()

            if not business:
                return Response(
                    {
                        "is_complete": False,
                        "data": None,
                        "message": "No business profile found.",
                    }
                )

            # Check for completeness (Required fields)
            required_fields = [
                business.business_name,
                business.business_email,
                business.business_phone,
                business.address,  # Foreign key check
            ]

            # Check address fields if address exists
            if business.address:
                required_fields.extend(
                    [
                        business.address.street,
                        business.address.city,
                        business.address.state,
                        business.address.zip_code,
                        business.address.country,
                    ]
                )

            is_complete = (
                all(bool(f) for f in required_fields) and user.onboarding_complete
            )

            # Serialize data for pre-filling
            business_data = BusinessProfileSerializer(business).data

            # Get social profiles
            social_profiles = SocialMediaProfileModel.objects.filter(bizness=business)
            social_data = SocialMediaProfileSerializer(social_profiles, many=True).data

            return Response(
                {
                    "is_complete": is_complete,
                    "data": {
                        "businessProfile": business_data,
                        "socialProfiles": social_data,
                        "userProfile": UserSerializer(user).data,
                    },
                    "message": "Business profile data retrieved.",
                }
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        print("DEBUG: OnboardingView.post called", flush=True)
        try:
            raw_data = request.data.get("data")
            print(
                f"DEBUG: raw_data received: {raw_data[:100] if raw_data else 'None'}",
                flush=True,
            )
            if not raw_data:
                return Response(
                    {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
                )

            payload = json.loads(raw_data)
            # csv_file = request.FILES.get("file") # Removed as per requirement
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_profile_data = payload.get("userProfile", {})
        business_profile_data = payload.get("businessProfile", {})
        social_profiles_data = payload.get("socialProfiles", [])

        try:
            print("DEBUG: Starting transaction...", flush=True)
            with transaction.atomic():
                # User Profile (validate, then update)
                user = request.user
                user_serializer = UserSerializer(
                    user, data=user_profile_data, partial=True
                )
                if not user_serializer.is_valid():
                    print(
                        f"DEBUG: User serializer errors: {user_serializer.errors}",
                        flush=True,
                    )
                    return Response(
                        {"user_errors": user_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user.name = user_profile_data.get("name") or user_profile_data.get(
                    "display_name"
                )
                user.phone_number = user_profile_data.get("phone_number")
                user.user_type = user_profile_data.get("user_type", "owner")
                user.save()

                print("DEBUG: User profile updated", flush=True)

                # Business Profile: validate via serializer and create with context owner
                business_serializer = BusinessProfileSerializer(
                    data=business_profile_data, context={"owner": request.user}
                )
                if not business_serializer.is_valid():
                    print(
                        f"DEBUG: Business serializer errors: {business_serializer.errors}",
                        flush=True,
                    )
                    return Response(
                        {"business_errors": business_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                business_instance = business_serializer.save()
                print("DEBUG: Business profile saved", flush=True)

                # Link business to user
                user.business_profile = business_instance
                user.save()

                # Social Profiles: validate each and bulk create
                social_objects = []
                for sp in social_profiles_data:
                    # Skip empty entries
                    if not sp.get("profile_url"):
                        continue
                    platform = sp.get("platform")
                    if platform == "Other" and sp.get("custom_platform"):
                        platform = sp.get("custom_platform")

                    # Optional: you can validate via serializer:
                    sp_serializer = SocialMediaProfileSerializer(
                        data={
                            "platform": platform,
                            "profile_url": sp.get("profile_url"),
                            "active": sp.get("active", True),
                            "can_be_used_for_marketing": sp.get(
                                "can_be_used_for_marketing", False
                            ),
                            "media_type": sp.get("media_type", "image"),
                        }
                    )
                    if not sp_serializer.is_valid():
                        # skip or return error — here we skip invalid entries
                        continue

                    social_objects.append(
                        SocialMediaProfileModel(
                            bizness=business_instance,
                            platform=platform,
                            profile_url=sp.get("profile_url"),
                            active=sp.get("active", True),
                            can_be_used_for_marketing=sp.get(
                                "can_be_used_for_marketing", False
                            ),
                            media_type=sp.get("media_type", "image"),
                        )
                    )
                if social_objects:
                    SocialMediaProfileModel.objects.bulk_create(social_objects)
                print("DEBUG: Social profiles saved", flush=True)

                # Mark onboarding complete on user profile
                try:
                    user.onboarding_complete = True
                    user.save(update_fields=["onboarding_complete"])
                except Exception:
                    # don't break onboarding if this fails, but log
                    pass

                return Response(
                    {"message": "Onboarding completed successfully"},
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve user and business profile data.
        """
        try:
            user = request.user
            business_profile = BusinessProfileModel.objects.filter(
                owner=request.user
            ).first()

            user_data = UserSerializer(user).data
            business_data = (
                BusinessProfileSerializer(business_profile).data
                if business_profile
                else None
            )

            return Response(
                {"user_profile": user_data, "business_profile": business_data}
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        """
        Update user and business profile data.
        """
        try:
            user_data = request.data.get("user_profile", {})
            business_data = request.data.get("business_profile", {})

            user = request.user
            business_profile = BusinessProfileModel.objects.filter(
                owner=request.user
            ).first()

            with transaction.atomic():
                # Update User Profile
                if user_data:
                    user_serializer = UserSerializer(user, data=user_data, partial=True)
                    if user_serializer.is_valid():
                        user_serializer.save()
                    else:
                        return Response(
                            {"user_errors": user_serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # Update Business Profile
                if business_data and business_profile:
                    # Handle nested address update if present
                    if "address" in business_data:
                        address_data = business_data.pop("address")
                        address_serializer = AddressSerializer(
                            business_profile.address, data=address_data, partial=True
                        )
                        if address_serializer.is_valid():
                            address_serializer.save()
                        else:
                            return Response(
                                {"address_errors": address_serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                    business_serializer = BusinessProfileSerializer(
                        business_profile, data=business_data, partial=True
                    )
                    if business_serializer.is_valid():
                        business_serializer.save()
                    else:
                        return Response(
                            {"business_errors": business_serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            return Response(
                {"message": "Profile updated successfully"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class POSConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the current POS connection status.
        """
        try:
            business_profile = BusinessProfileModel.objects.filter(
                owner=request.user
            ).first()
            if not business_profile:
                return Response(
                    {"error": "Business profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response({"clover_connected": business_profile.clover_connected})
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Toggle the POS connection status.
        """
        try:
            business_profile = BusinessProfileModel.objects.filter(
                owner=request.user
            ).first()
            if not business_profile:
                return Response(
                    {"error": "Business profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Toggle the status
            business_profile.clover_connected = not business_profile.clover_connected
            business_profile.save()

            return Response(
                {
                    "message": "POS connection status updated",
                    "clover_connected": business_profile.clover_connected,
                }
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmployeeManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all employees for the current business."""
        business = BusinessProfileModel.objects.filter(owner=request.user).first()
        if not business:
            return Response(
                {"error": "Business not found"}, status=status.HTTP_404_NOT_FOUND
            )

        employees = User.objects.filter(business_profile=business, is_employee=True)
        data = UserSerializer(employees, many=True).data
        return Response(data)

    def post(self, request):
        """Create a new employee."""
        business = BusinessProfileModel.objects.filter(owner=request.user).first()
        if not business:
            return Response(
                {"error": "Business not found"}, status=status.HTTP_404_NOT_FOUND
            )

        email = request.data.get("email")
        password = request.data.get("password")
        name = request.data.get("name")

        if not email or not password or not name:
            return Response(
                {"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                user = User.objects.create_user(email=email, password=password)
                user.name = name
                user.user_type = "employee"
                user.is_employee = True
                user.business_profile = business
                user.onboarding_complete = True
                user.save()

            return Response(
                {"message": "Employee created successfully"},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk=None):
        """Delete an employee."""
        if not pk:
            return Response(
                {"error": "ID required"}, status=status.HTTP_400_BAD_REQUEST
            )

        business = BusinessProfileModel.objects.filter(owner=request.user).first()
        if not business:
            return Response(
                {"error": "Business not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Check if user is an employee of this business
            user = User.objects.get(id=pk, business_profile=business, is_employee=True)
            user.delete()
            return Response({"message": "Employee deleted successfully"})
        except User.DoesNotExist:
            return Response(
                {"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND
            )
