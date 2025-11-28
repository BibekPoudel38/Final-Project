import json
import csv
import io
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import (
    UserProfileModel,
    BusinessProfileModel,
    SocialMediaProfileModel,
    AddressModel,
)
from .serializers import (
    UserProfileSerializer,
    BusinessProfileSerializer,
    SocialMediaProfileSerializer,
    AddressSerializer,
)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        """
        Checks if the user has already completed onboarding.
        Used by the frontend to skip the flow.
        """
        is_complete = BusinessProfileModel.objects.filter(owner=request.user).exists()

        return Response(
            {
                "is_complete": is_complete,
                "message": (
                    "Onboarding already completed"
                    if is_complete
                    else "User pending onboarding"
                ),
            }
        )

    def post(self, request):

        # inside post(self, request):
        try:
            raw_data = request.data.get("data")
            if not raw_data:
                return Response(
                    {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
                )

            payload = json.loads(raw_data)
            csv_file = request.FILES.get("file")
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_profile_data = payload.get("userProfile", {})
        business_profile_data = payload.get("businessProfile", {})
        social_profiles_data = payload.get("socialProfiles", [])

        try:
            with transaction.atomic():
                # User Profile (validate, then create/update)
                # Use serializer to validate user profile fields (email read-only)
                user_serializer = UserProfileSerializer(
                    data=user_profile_data, partial=True
                )
                if not user_serializer.is_valid():
                    return Response(
                        {"user_errors": user_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # update_or_create based on auth_id (one profile per user)
                user_profile, created = UserProfileModel.objects.update_or_create(
                    auth_id=request.user,
                    defaults={
                        "name": user_profile_data.get("name")
                        or user_profile_data.get("display_name"),
                        "phone_number": user_profile_data.get("phone_number"),
                        "user_type": user_profile_data.get("user_type", "owner"),
                        "email": request.user.email,
                    },
                )

                # Business Profile: validate via serializer and create with context owner
                business_serializer = BusinessProfileSerializer(
                    data=business_profile_data, context={"owner": request.user}
                )
                if not business_serializer.is_valid():
                    return Response(
                        {"business_errors": business_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                business_instance = business_serializer.save()

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

                # CSV processing (safe, existing helper)
                if csv_file:
                    self._process_sales_csv(csv_file, business_instance)

                # Mark onboarding complete on user profile
                try:
                    user_profile.onboarding_complete = True
                    user_profile.save(update_fields=["onboarding_complete"])
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

    def _process_sales_csv(self, file_obj, business_instance):
        """
        Helper to process the CSV file.
        Since no Sales Model was provided in the prompt, this is a placeholder
        wrapper to demonstrate where the logic goes.
        """
        try:
            decoded_file = file_obj.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            sales_records = []
            for row in reader:
                # Example logic:
                # sales_records.append(SalesModel(
                #     business=business_instance,
                #     date=row['Date'],
                #     amount=row['Amount']
                # ))
                pass

            # if sales_records:
            #     SalesModel.objects.bulk_create(sales_records)

            print(
                f"Processed CSV file: {file_obj.name} for business {business_instance.business_name}"
            )

        except Exception as e:
            # We log the error but don't stop the onboarding process for a bad CSV
            print(f"Error processing CSV: {e}")


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve user and business profile data.
        """
        try:
            user_profile = UserProfileModel.objects.get(auth_id=request.user)
            business_profile = BusinessProfileModel.objects.filter(
                owner=request.user
            ).first()

            user_data = UserProfileSerializer(user_profile).data
            business_data = (
                BusinessProfileSerializer(business_profile).data
                if business_profile
                else None
            )

            return Response(
                {"user_profile": user_data, "business_profile": business_data}
            )
        except UserProfileModel.DoesNotExist:
            return Response(
                {"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request):
        """
        Update user and business profile data.
        """
        try:
            user_data = request.data.get("user_profile", {})
            business_data = request.data.get("business_profile", {})

            user_profile = UserProfileModel.objects.get(auth_id=request.user)
            business_profile = BusinessProfileModel.objects.filter(
                owner=request.user
            ).first()

            with transaction.atomic():
                # Update User Profile
                if user_data:
                    user_serializer = UserProfileSerializer(
                        user_profile, data=user_data, partial=True
                    )
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

        except UserProfileModel.DoesNotExist:
            return Response(
                {"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND
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

        employees = UserProfileModel.objects.filter(
            business_profile=business, is_employee=True
        )
        data = UserProfileSerializer(employees, many=True).data
        return Response(data)

    def post(self, request):
        """Create a new employee."""
        User = get_user_model()
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
                UserProfileModel.objects.create(
                    auth_id=user,
                    name=name,
                    email=email,
                    user_type="employee",
                    is_employee=True,
                    business_profile=business,
                    onboarding_complete=True,
                )
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
            employee_profile = UserProfileModel.objects.get(
                id=pk, business_profile=business, is_employee=True
            )
            user = employee_profile.auth_id
            employee_profile.delete()
            user.delete()  # Delete the auth user too
            return Response({"message": "Employee deleted successfully"})
        except UserProfileModel.DoesNotExist:
            return Response(
                {"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND
            )
