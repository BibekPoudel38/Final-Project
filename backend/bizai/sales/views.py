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
        queryset = (
            SalesModel.objects.filter(is_active=True)
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
        # Total Revenue
        total_revenue = (
            SalesModel.objects.aggregate(Sum("revenue"))["revenue__sum"] or 0
        )

        # Top Product
        top_product_data = (
            SalesModel.objects.values("prod_id__item_name")
            .annotate(total_sold=Sum("quantity_sold"))
            .order_by("-total_sold")
            .first()
        )
        top_product = (
            top_product_data["prod_id__item_name"] if top_product_data else "N/A"
        )

        # Sales Trend (Last 7 days with sales)
        trend_query = (
            SalesModel.objects.values("sale_date")
            .annotate(revenue=Sum("revenue"))
            .order_by("-sale_date")[:7]
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
            }
        )


class TrainModelView(APIView):
    """
    Trigger model retraining with current sales data.
    """

    def post(self, request):
        try:
            # Fetch all active sales
            sales = (
                SalesModel.objects.filter(is_active=True)
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
            payload = {"business_id": "biz_001", "data": training_data}  # Default

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
                    TrainingMetrics.objects.create(
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

        latest = TrainingMetrics.objects.order_by("-created_at").first()
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
            if "business_id" not in payload:
                payload["business_id"] = "biz_001"

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
            # Global Stats
            total_revenue = (
                SalesModel.objects.aggregate(Sum("revenue"))["revenue__sum"] or 0
            )
            total_sales_count = SalesModel.objects.count()

            # Top Product
            top_product_data = (
                SalesModel.objects.values("prod_id__item_name")
                .annotate(total_sold=Sum("quantity_sold"))
                .order_by("-total_sold")
                .first()
            )
            top_product = (
                top_product_data["prod_id__item_name"] if top_product_data else "N/A"
            )

            # Recent Transactions (Last 5)
            recent_sales = (
                SalesModel.objects.filter(is_active=True)
                .select_related("prod_id")
                .order_by("-sale_date")[:5]
            )
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
