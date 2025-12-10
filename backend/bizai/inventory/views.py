from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, F
from rest_framework.permissions import IsAuthenticated
from merchant.models import BusinessProfileModel
import django.db.models as dj_models
from .models import InventorModel
from sales.models import SalesModel
from .serializers import InventorySerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
import csv
import csv
import io
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from django.utils import timezone
from datetime import timedelta

# Create your views here.


class InventoryDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InventorModel.objects.filter(
            dj_models.Q(user=request.user) | dj_models.Q(business__owner=request.user)
        )
        # Calculate total value: sum of quantity * cost_price
        total_count = qs.count()
        total_value_data = qs.aggregate(total_val=Sum(F("quantity") * F("cost_price")))
        total_value = total_value_data["total_val"] or 0

        low_stock_items = qs.filter(quantity__lt=F("min_quantity")).count()

        # Top Seller Item logic limited to the user's scope
        top_seller_data = (
            SalesModel.objects.filter(
                dj_models.Q(user=request.user)
                | dj_models.Q(business__owner=request.user)
            )
            .values("prod_id")
            .annotate(total_sold=Sum("quantity_sold"))
            .order_by("-total_sold")
            .first()
        )

        top_seller_item = None
        if top_seller_data:
            try:
                item = InventorModel.objects.get(id=top_seller_data["prod_id"])
                top_seller_item = InventorySerializer(item).data
                top_seller_item["total_sold"] = top_seller_data["total_sold"]
            except InventorModel.DoesNotExist:
                pass

        data = {
            "total_count": total_count,
            "total_value": total_value,
            "low_stock_items": low_stock_items,
            "top_seller_item": top_seller_item,
        }
        return Response(data)


class InventoryCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InventorModel.objects.filter(
            dj_models.Q(user=request.user) | dj_models.Q(business__owner=request.user)
        )
        category_data = (
            qs.values("type")
            .annotate(count=Count("id"), total_quantity=Sum("quantity"))
            .order_by("-total_quantity")
        )
        return Response(category_data)


class InventoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Determine the business for this user. Prefer owner relationship.
        business = BusinessProfileModel.objects.filter(owner=request.user).first()
        if not business:
            # Fallback: try matching by email
            business = BusinessProfileModel.objects.filter(
                business_email=request.user.email
            ).first()

        if not business:
            return Response(
                {"error": "No business found for user. Link user to a business first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce one-user -> one-business rule for inventory creation: if user already has items tied to a different business, block
        existing = (
            InventorModel.objects.filter(user=request.user)
            .exclude(business=business)
            .exists()
        )
        if existing:
            return Response(
                {"error": "This user is already associated with a different business."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print(f"DEBUG CREATE DATA RAW: {request.data}")
        print(f"DEBUG CREATE DATA TYPE: {type(request.data)}")
        # Handle QueryDict (multipart) vs standard dict (json)
        if hasattr(request.data, "dict"):
            data = request.data.dict()
        else:
            data = request.data
        print(f"DEBUG CREATE DATA PROCESSED: {data}")
        serializer = InventorySerializer(data=data)
        if serializer.is_valid():
            instance = serializer.save(user=request.user, business=business)
            return Response(
                InventorySerializer(instance).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryListView(ListAPIView):
    serializer_class = InventorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = []
    search_fields = ["item_name", "item_description"]
    ordering_fields = ["quantity", "selling_price", "created_at"]
    ordering = ["-created_at"]  # Default ordering
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InventorModel.objects.filter(
            dj_models.Q(user=self.request.user)
            | dj_models.Q(business__owner=self.request.user)
        ).distinct()


from django.http import HttpResponse


class InventoryExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="inventory.csv"'

        writer = csv.writer(response)
        # Get all field names from the model
        fields = [field.name for field in InventorModel._meta.fields]
        writer.writerow(fields)

        qs = InventorModel.objects.filter(
            dj_models.Q(user=request.user) | dj_models.Q(business__owner=request.user)
        )
        for item in qs:
            row = [getattr(item, field) for field in fields]
            writer.writerow(row)

        return response


class InventoryImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith(".csv"):
            return Response(
                {"error": "File must be CSV"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            decoded_file = file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            created_count = 0
            updated_count = 0
            errors = []

            for row in reader:
                # Assuming 'item_name' or 'id' is unique identifier.
                # If ID is present and exists, update. Else create.
                # However, ID is auto-field usually. Let's check if 'id' is in row and valid.

                item_id = row.get("id")
                item_data = {
                    k: v for k, v in row.items() if k != "id" and v != ""
                }  # Filter empty strings

                # Handle foreign keys if necessary.
                # Note: 'business' and 'user' are required fields in InventorModel.
                # If they are not in CSV, we might need to get them from request context or fail.
                # For now, assuming CSV contains all required fields or we can't import easily without context.
                # BUT, usually import is done by a logged in user for their business.
                # Let's assume we need to set business and user from request if not in CSV?
                # The model has business and user.
                # Let's try to get them from the row. If not present, we might fail validation.

                # Simple approach: Try to save via serializer to handle validation

                # Ensure business & user are set to the requesting user's business
                business = BusinessProfileModel.objects.filter(
                    owner=request.user
                ).first()
                if not business:
                    business = BusinessProfileModel.objects.filter(
                        business_email=request.user.email
                    ).first()
                if not business:
                    errors.append("No business found for user; import aborted")
                    break

                instance = None
                if item_id:
                    try:
                        instance = InventorModel.objects.get(id=item_id)
                    except InventorModel.DoesNotExist:
                        pass

                # attach business and user if not provided
                item_data.setdefault("business", business.id)
                item_data.setdefault("user", request.user.id)

                serializer = InventorySerializer(instance, data=item_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    if instance:
                        updated_count += 1
                    else:
                        created_count += 1
                else:
                    errors.append(
                        f"Row {row.get('item_name', 'Unknown')}: {serializer.errors}"
                    )

            return Response(
                {
                    "message": "Import processed",
                    "created": created_count,
                    "updated": updated_count,
                    "errors": errors,
                }
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    queryset = InventorModel.objects.all()

    def get_queryset(self):
        return InventorModel.objects.filter(
            dj_models.Q(user=self.request.user)
            | dj_models.Q(business__owner=self.request.user)
        )


class InventoryUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            item = InventorModel.objects.get(
                dj_models.Q(id=pk)
                & (
                    dj_models.Q(user=request.user)
                    | dj_models.Q(business__owner=request.user)
                )
            )
        except InventorModel.DoesNotExist:
            return Response(
                {"error": "Item not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InventorySerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryItemAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Verify item access
        try:
            item = InventorModel.objects.get(
                dj_models.Q(id=pk)
                & (
                    dj_models.Q(user=request.user)
                    | dj_models.Q(business__owner=request.user)
                )
            )
        except InventorModel.DoesNotExist:
            return Response(
                {"error": "Item not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get sales for the last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        sales_data = (
            SalesModel.objects.filter(
                prod_id=item, sale_date__range=[start_date, end_date]
            )
            .values("sale_date")
            .annotate(total_sold=Sum("quantity_sold"), total_revenue=Sum("revenue"))
            .order_by("sale_date")
        )

        # Format for frontend chart
        chart_data = []
        current_date = start_date
        sales_dict = {entry["sale_date"]: entry for entry in sales_data}

        while current_date <= end_date:
            entry = sales_dict.get(current_date, {"total_sold": 0, "total_revenue": 0})
            chart_data.append(
                {
                    "date": current_date.strftime("%b %d"),
                    "sold": float(entry["total_sold"] or 0),
                    "revenue": float(entry["total_revenue"] or 0),
                }
            )
            current_date += timedelta(days=1)

        return Response(chart_data)
