from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Count, Q
from sales.models import SalesModel
import requests
import json


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SalesListView(APIView):
    """
    REST API endpoint to fetch sales data for the authenticated user's business.
    """

    def get(self, request):
        # Get query parameters for filtering
        search = request.GET.get("search", "")
        date_from = request.GET.get("date_from", "")
        date_to = request.GET.get("date_to", "")
        weather = request.GET.get("weather", "")

        # Base queryset
        # Base queryset
        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=401)

        queryset = (
            SalesModel.objects.filter(is_active=True, prod_id__user=request.user)
            .select_related("prod_id")
            .prefetch_related("holidays")
        )

        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(sales_uid__icontains=search) | Q(prod_id__item_name__icontains=search)
            )

        if date_from:
            queryset = queryset.filter(sale_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(sale_date__lte=date_to)

        if weather:
            queryset = queryset.filter(weather_condition=weather)

        # Serialize data
        # Pagination
        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(
            queryset.order_by("-sale_date"), request
        )

        sales_data = []
        for sale in result_page:
            holidays = ", ".join([h.name for h in sale.holidays.all()])

            sales_data.append(
                {
                    "id": sale.id,
                    "product_id": sale.prod_id.item_name if sale.prod_id else "N/A",
                    "date": sale.sale_date.strftime("%m/%d/%Y"),
                    "units_sold": float(sale.quantity_sold),
                    "revenue": float(sale.revenue),
                    "customer_flow": sale.customer_flow,
                    "weather_temp": float(sale.weather_temperature),
                    "weather_condition": sale.weather_condition,
                    "holiday_name": holidays,
                    "is_store_open": 1,
                    "is_on_sale": 1 if sale.was_on_sale else 0,
                    "discount_percentage": (
                        float(sale.discount_percentage)
                        if sale.discount_percentage
                        else 0
                    ),
                    "flow_students": sale.flow_students or 0,
                    "flow_families": sale.flow_family or 0,
                    "flow_seniors": sale.flow_adults or 0,
                }
            )

        return paginator.get_paginated_response(sales_data)


class SalesInsightsView(APIView):
    """
    Efficiently aggregates sales data for the dashboard.
    """

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=401)

        # Base filter for this user
        user_sales = SalesModel.objects.filter(
            prod_id__user=request.user, is_active=True
        )

        # Total Revenue
        total_revenue = user_sales.aggregate(Sum("revenue"))["revenue__sum"] or 0

        # Top Product
        top_product_data = (
            user_sales.values("prod_id__item_name")
            .annotate(total_sold=Sum("quantity_sold"))
            .order_by("-total_sold")
            .first()
        )
        top_product = (
            top_product_data["prod_id__item_name"] if top_product_data else "N/A"
        )

        # Sales Trend (Daily revenue for entire dataset - or last 30 days?)
        # User wants "entire dataset", but strictly linear chart of 365 days is messy.
        # Let's return last 30 days for trend, or aggregated by month if > 90 days?
        # For now, let's stick to the user's request "metrics should consider entire dataset".
        # Total Revenue and Top Product are already entire dataset.
        # Trend Chart usually implies "recent" or "over time". All time daily might be too big.
        # Let's keep trend as is (Last 7 days) or maybe extend to 14/30?
        # Actually, let's just make sure "Weather Impact" is entire dataset.

        # Weather Impact
        weather_impact_query = (
            user_sales.values("weather_condition")
            .annotate(revenue=Sum("revenue"))
            .order_by("-revenue")
        )
        weather_impact = [
            {"name": item["weather_condition"] or "Unknown", "revenue": item["revenue"]}
            for item in weather_impact_query
        ]

        # Sales Trend (Let's increase to 30 days for better context)
        trend_query = (
            user_sales.values("sale_date")
            .annotate(revenue=Sum("revenue"))
            .order_by("-sale_date")[:30]
        )
        trend_data = [
            {"name": item["sale_date"].strftime("%m/%d"), "revenue": item["revenue"]}
            for item in reversed(trend_query)
        ]

        return Response(
            {
                "total_revenue": total_revenue,
                "top_product": top_product,
                "sales_trend": trend_data,
                "weather_impact": weather_impact,
            }
        )


class TrainModelView(APIView):
    """
    Trigger model retraining with current sales data.
    """

    def post(self, request):
        try:
            # Fetch all active sales
            # Fetch all active sales for this user
            if not request.user.is_authenticated:
                return Response({"error": "Unauthorized"}, status=401)

            sales = (
                SalesModel.objects.filter(is_active=True, prod_id__user=request.user)
                .select_related("prod_id")
                .prefetch_related("holidays")
            )

            training_data = []
            for sale in sales:
                holidays_list = [h.name for h in sale.holidays.all()]
                training_data.append(
                    {
                        "date": sale.sale_date.strftime("%Y-%m-%d"),
                        "product_id": sale.prod_id.item_name,  # Use Name to match Simulator
                        "sales_amount": float(sale.revenue),
                        "sales_quantity": int(sale.quantity_sold),
                        "weather_condition": sale.weather_condition,
                        "temperature": float(sale.weather_temperature),
                        "fuel_price": 4.0
                        + (float(sale.weather_temperature) % 2),  # Simulated Fuel Price
                        "has_offers": 1 if sale.was_on_sale else 0,
                        "offer_amount": (
                            float(sale.discount_percentage)
                            if sale.discount_percentage
                            else 0.0
                        ),
                        "is_holiday": 1 if holidays_list else 0,
                        "holidays_list": holidays_list,
                        "festivals": [],
                        "local_events": [],
                    }
                )

            if not training_data:
                return Response(
                    {
                        "status": "error",
                        "message": "No sales data available for training.",
                    },
                    status=400,
                )

            # Send to Prediction Model
            # Secure: Use User ID as business_id
            if not request.user.is_authenticated:
                return Response({"error": "Unauthorized"}, status=401)

            business_id = str(request.user.id)
            payload = {"business_id": business_id, "data": training_data}

            # Prediction Service URL
            urls_to_try = [
                "http://prediction:8080/retrain",
                "http://localhost:8080/retrain",
                "http://host.docker.internal:8080/retrain",
            ]
            response = None
            last_error = None

            for url in urls_to_try:
                try:
                    response = requests.post(url, json=payload, timeout=300)
                    break
                except requests.exceptions.ConnectionError as e:
                    last_error = e
                    continue

            if response is None:
                return Response(
                    {
                        "status": "error",
                        "message": f"Prediction service is not running. Tried localhost and host.docker.internal. Error: {str(last_error)}",
                    },
                    status=503,
                )

            if response.status_code == 200:
                data = response.json()

                # Save Metrics
                if "metrics" in data:
                    from sales.models import TrainingMetrics

                    metrics = data["metrics"]
                    metrics = data["metrics"]
                    TrainingMetrics.objects.create(
                        user=request.user,
                        accuracy=metrics.get("accuracy", 0.0),
                        loss=metrics.get("loss", 0.0),
                        mae=metrics.get("mae"),
                        mse=metrics.get("mse"),
                        rmse=metrics.get("rmse"),
                        mape=metrics.get("mape"),
                        r2_score=metrics.get("r2_score"),
                        explained_variance=metrics.get("explained_variance"),
                        model_version=metrics.get("model_version", "unknown"),
                        training_info=data.get("training_info"),
                    )

                return Response(
                    {
                        "status": "success",
                        "message": "Model trained successfully.",
                        "details": data,
                    }
                )
            else:
                return Response(
                    {
                        "status": "error",
                        "message": "Prediction service failed.",
                        "details": response.text,
                    },
                    status=500,
                )

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)


class TrainingMetricsView(APIView):
    """
    Get the latest training metrics.
    """

    def get(self, request):
        from sales.models import TrainingMetrics

        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=401)

        latest = (
            TrainingMetrics.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        if latest:
            return Response(
                {
                    "accuracy": latest.accuracy,
                    "loss": latest.loss,
                    "mae": latest.mae,
                    "mse": latest.mse,
                    "rmse": latest.rmse,
                    "mape": latest.mape,
                    "r2_score": latest.r2_score,
                    "explained_variance": latest.explained_variance,
                    "model_version": latest.model_version,
                    "last_trained": latest.created_at,
                    "training_info": latest.training_info,
                }
            )
        return Response(
            {
                "accuracy": 0.0,
                "loss": 0.0,
                "mae": 0.0,
                "mse": 0.0,
                "rmse": 0.0,
                "mape": 0.0,
                "r2_score": 0.0,
                "explained_variance": 0.0,
                "model_version": "None",
                "last_trained": None,
                "training_info": None,
            }
        )


class ScenarioPredictionView(APIView):
    """
    Proxy for interactive scenario prediction.
    """

    def post(self, request):
        try:
            # Forward the request to the prediction service
            payload = request.data

            # Ensure business_id is present
            # Ensure business_id is present and secure
            if not request.user.is_authenticated:
                return Response({"error": "Unauthorized"}, status=401)

            # FORCE override business_id with the user's ID
            payload["business_id"] = str(request.user.id)

            # Prediction Service URL
            urls_to_try = [
                "http://prediction:8080/predict_custom",
                "http://localhost:8080/predict_custom",
                "http://host.docker.internal:8080/predict_custom",
                "http://host.docker.internal:8080/predict_custom",
            ]

            response = None
            last_error = None

            for url in urls_to_try:
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    break
                except requests.exceptions.ConnectionError as e:
                    last_error = e
                    continue

            if response is None:
                return Response(
                    {
                        "error": f"Prediction service not reachable. Last error: {str(last_error)}"
                    },
                    status=503,
                )

            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {"error": "Prediction service error", "details": response.text},
                    status=response.status_code,
                )

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class SalesAIChatView(APIView):
    """
    Handle natural language queries about sales data by proxying to the LLM service with context.
    """

    def post(self, request):
        query = request.data.get("query", "")
        if not query:
            return Response({"message": "Query is required"}, status=400)

        try:
            # 1. Gather Context
            if not request.user.is_authenticated:
                return Response({"error": "Unauthorized"}, status=401)

            user_sales = SalesModel.objects.filter(
                prod_id__user=request.user, is_active=True
            )

            # Global Stats
            total_revenue = user_sales.aggregate(Sum("revenue"))["revenue__sum"] or 0
            total_sales_count = user_sales.count()

            # Top Product
            top_product_data = (
                user_sales.values("prod_id__item_name")
                .annotate(total_sold=Sum("quantity_sold"))
                .order_by("-total_sold")
                .first()
            )
            top_product = (
                top_product_data["prod_id__item_name"] if top_product_data else "N/A"
            )

            # Recent Transactions (Last 5)
            recent_sales = user_sales.select_related("prod_id").order_by("-sale_date")[
                :5
            ]
            recent_sales_list = []
            for s in recent_sales:
                recent_sales_list.append(
                    {
                        "date": s.sale_date.strftime("%Y-%m-%d"),
                        "product_name": s.prod_id.item_name,
                        "revenue_usd": float(s.revenue),
                        "units_sold_count": float(s.quantity_sold),
                    }
                )

            context = {
                "total_revenue_usd": float(total_revenue),
                "total_transactions_count": total_sales_count,
                "top_selling_product": top_product,
                "recent_sales_transactions": recent_sales_list,
            }

            # 2. Construct Prompt
            system_prompt = f"""
            You are a helpful AI assistant for a business owner. 
            Here is the current sales data context:
            {json.dumps(context, indent=2)}
            
            Data Dictionary:
            - revenue_usd: The total money earned in USD.
            - units_sold_count: The number of individual items sold.
            
            Answer the user's question based strictly on this data. Do not confuse revenue with units sold.
            Be concise and professional.
            """

            combined_query = f"{system_prompt}\n\nUser Question: {query}"

            payload = {"query": combined_query, "session_id": "sales_assistant_proxy"}

            # 3. Call LLM Service
            urls_to_try = [
                "http://final_project_llm:5000/chat",
                "http://llm:5000/chat",
                "http://localhost:5000/chat",
                "http://host.docker.internal:5000/chat",
            ]

            response_data = {
                "answer": "AI Service Unavailable. Please check if the LLM service is running."
            }

            for url in urls_to_try:
                try:
                    resp = requests.post(url, json=payload, timeout=30)
                    if resp.status_code == 200:
                        response_data = resp.json()
                        break
                except:
                    continue

            return Response(response_data)

        except Exception as e:
            return Response(
                {"message": f"Error processing AI request: {str(e)}"}, status=500
            )


class SalesImportView(APIView):
    """
    Import Sales Data from CSV.
    Optimized for performance using bulk_create.
    """

    def post(self, request):
        import csv
        import io
        import uuid
        from inventory.models import InventorModel
        from sales.models import SalesModel

        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=401)

        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=400)

        file = request.FILES["file"]
        if not file.name.endswith(".csv"):
            return Response({"error": "File must be a CSV"}, status=400)

        try:
            decoded_file = file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            rows = list(reader)

            if not rows:
                return Response({"error": "Empty CSV file"}, status=400)

            # 1. Collect all sales_uids to check duplicates in one query
            # Generate UIDs for rows that don't have them
            row_data = []
            uids_to_check = []

            # Pre-process rows
            for row in rows:
                sales_uid = (
                    row.get("sales_uid") or row.get("uid") or row.get("Transaction ID")
                )
                if not sales_uid:
                    sales_uid = f"auto_{uuid.uuid4().hex[:12]}"

                row["clean_uid"] = sales_uid
                uids_to_check.append(sales_uid)
                row_data.append(row)

            # Fetch existing UIDs
            existing_uids = set(
                SalesModel.objects.filter(sales_uid__in=uids_to_check).values_list(
                    "sales_uid", flat=True
                )
            )

            # Filter out duplicates
            new_rows = [r for r in row_data if r["clean_uid"] not in existing_uids]

            if not new_rows:
                return Response(
                    {
                        "status": "success",
                        "created": 0,
                        "skipped": len(rows),
                        "message": "All records were duplicates.",
                    }
                )

            # 2. Handle Inventory (Products)
            # Collect all product names
            product_names = set()
            for row in new_rows:
                p_name = row.get("product_id") or row.get("Product Name")
                if p_name:
                    product_names.add(p_name)

            # Fetch existing inventory for this user
            existing_inventory = InventorModel.objects.filter(
                user=request.user, item_name__in=product_names
            )
            inventory_map = {item.item_name: item for item in existing_inventory}

            # Identify missing products
            missing_products = product_names - set(inventory_map.keys())

            # Create missing products in bulk?
            # InventorModel might have other required fields, but we set defaults.
            # bulk_create doesn't return IDs in some DBs/Django versions cleanly for mapping,
            # so we'll loop create for missing ones (usually few types) or assume they are few.
            # Since product types are usually < 100, loop create is fast enough.

            # Fetch User's Business (Required for Inventory)
            from merchant.models import BusinessProfileModel

            user_business = BusinessProfileModel.objects.filter(
                owner=request.user
            ).first()
            if not user_business and missing_products:
                return Response(
                    {"error": "No Business Profile found. Please complete onboarding."},
                    status=400,
                )

            for prod_name in missing_products:
                # Find a sample row to get price?
                sample_row = next(
                    (
                        r
                        for r in new_rows
                        if (
                            r.get("product_id") == prod_name
                            or r.get("Product Name") == prod_name
                        )
                    ),
                    {},
                )
                rev = float(sample_row.get("revenue") or sample_row.get("Amount") or 0)
                units = float(
                    sample_row.get("units_sold") or sample_row.get("Units") or 1
                )
                est_price = rev / units if units else 0

                item = InventorModel.objects.create(
                    user=request.user,
                    business=user_business,
                    item_name=prod_name,
                    item_description="Auto-created from Sales Import",
                    quantity=0,
                    quantity_unit="units",
                    selling_price=est_price,
                    cost_price=0,
                    type="Imported",
                    min_quantity=0,
                    is_active=True,
                )
                inventory_map[prod_name] = item

            # 3. Create Sale Objects
            sales_to_create = []
            errors = []

            for row in new_rows:
                try:
                    product_name = row.get("product_id") or row.get("Product Name")
                    date_val = row.get("date") or row.get("Date")
                    revenue = float(row.get("revenue") or row.get("Amount") or 0)
                    units = float(row.get("units_sold") or row.get("Units") or 0)

                    if not all([product_name, date_val]):
                        continue

                    inv_item = inventory_map.get(product_name)
                    if not inv_item:
                        continue  # Should not happen

                    sales_to_create.append(
                        SalesModel(
                            sales_uid=row["clean_uid"],
                            prod_id=inv_item,
                            sale_date=date_val,
                            quantity_sold=units,
                            revenue=revenue,
                            customer_flow=int(float(row.get("customer_flow", 0))),
                            weather_temperature=float(
                                row.get("weather_temp")
                                or row.get("temperature")
                                or 25.0
                            ),
                            weather_condition=row.get("weather_condition", "Sunny"),
                            discount_percentage=float(
                                row.get("discount_percentage", 0)
                            ),
                            is_active=True,
                        )
                    )
                except Exception as e:
                    errors.append(str(e))

            # Bulk Create
            SalesModel.objects.bulk_create(sales_to_create, batch_size=1000)

            return Response(
                {
                    "status": "success",
                    "created": len(sales_to_create),
                    "skipped": len(rows) - len(sales_to_create),
                    "errors": errors[:5],
                }
            )

        except Exception as e:
            return Response({"error": f"Failed to process CSV: {str(e)}"}, status=500)
