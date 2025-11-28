"""
Response formatter that classifies and structures data for frontend rendering
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseFormatter:
    """Analyzes GraphQL responses and formats them for optimal frontend display."""

    @staticmethod
    def analyze_and_format(
        graphql_result: Dict[str, Any], user_query: str
    ) -> Dict[str, Any]:
        """
        Analyze the GraphQL result and user query to determine the best display format.

        Returns a structured response with:
        - display_type: 'text', 'table', 'chart', 'metric', 'list'
        - data: formatted data ready for frontend
        - metadata: additional info for rendering
        """

        # Check for prediction result
        if graphql_result.get("type") == "prediction":
            return ResponseFormatter._format_prediction_response(graphql_result)

        # Extract data from GraphQL response
        if "data" not in graphql_result:
            return {
                "display_type": "text",
                "data": {"text": "No data available"},
                "metadata": {},
            }

        data = graphql_result["data"]

        # Determine what type of data we have
        if "allInventory" in data:
            return ResponseFormatter._format_inventory_response(
                data["allInventory"], user_query
            )
        elif "allSuppliers" in data:
            return ResponseFormatter._format_supplier_response(
                data["allSuppliers"], user_query
            )
        elif "allSales" in data:
            return ResponseFormatter._format_sales_response(
                data["allSales"], user_query
            )
        elif "salesReport" in data:
            return ResponseFormatter._format_sales_report(
                data["salesReport"], user_query
            )
        else:
            return {
                "display_type": "text",
                "data": {"text": json.dumps(data, indent=2)},
                "metadata": {},
            }

    @staticmethod
    def _format_inventory_response(
        inventory_data: Dict, user_query: str
    ) -> Dict[str, Any]:
        """Format inventory data based on query intent."""
        items = [edge["node"] for edge in inventory_data.get("edges", [])]

        if not items:
            return {
                "display_type": "text",
                "data": {"text": "No inventory items found."},
                "metadata": {},
            }

        query_lower = user_query.lower()

        # Detect query intent and choose appropriate visualization

        # 1. METRICS - Single numbers or aggregates
        if any(
            word in query_lower
            for word in ["total", "count", "how many", "sum", "average"]
        ):
            return ResponseFormatter._format_as_metrics(items, user_query)

        # 2. CHART - Comparisons, distributions, trends
        elif any(
            word in query_lower
            for word in [
                "compare",
                "distribution",
                "by type",
                "by category",
                "breakdown",
                "chart",
                "graph",
            ]
        ):
            return ResponseFormatter._format_as_chart(items, user_query)

        # 3. TABLE - Lists with multiple fields
        elif len(items) > 1 and len(items[0].keys()) > 3:
            return ResponseFormatter._format_as_table(items, user_query)

        # 4. LIST - Simple lists
        elif len(items) > 1:
            return ResponseFormatter._format_as_list(items, user_query)

        # 5. CARD - Single item details
        elif len(items) == 1:
            return ResponseFormatter._format_as_card(items[0], user_query)

        # Default to table
        return ResponseFormatter._format_as_table(items, user_query)

    @staticmethod
    def _format_sales_response(sales_data: Dict, user_query: str) -> Dict[str, Any]:
        """Format sales data based on query intent."""
        items = [edge["node"] for edge in sales_data.get("edges", [])]

        if not items:
            return {
                "display_type": "text",
                "data": {"text": "No sales records found."},
                "metadata": {},
            }

        query_lower = user_query.lower()

        # 1. METRICS - Aggregates
        if any(
            word in query_lower
            for word in ["total", "sum", "average", "metrics", "revenue", "how much"]
        ):
            return ResponseFormatter._format_as_metrics(items, user_query)

        # 2. CHART - Trends and distributions
        elif any(
            word in query_lower
            for word in [
                "trend",
                "chart",
                "graph",
                "plot",
                "over time",
                "by date",
                "by weather",
                "by promotion",
                "distribution",
            ]
        ):
            return ResponseFormatter._format_as_chart(items, user_query)

        # 3. TABLE - Detailed listing
        elif len(items) > 1:
            return ResponseFormatter._format_as_table(items, user_query)

        # 4. CARD - Single sale details
        elif len(items) == 1:
            return ResponseFormatter._format_as_card(items[0], user_query)

        return ResponseFormatter._format_as_table(items, user_query)

    @staticmethod
    def _format_as_metrics(items: List[Dict], query: str) -> Dict[str, Any]:
        """Format as metric cards (KPIs)."""
        metrics = []

        # Calculate various metrics
        total_items = len(items)

        # Check if this is sales data (has revenue) or inventory data
        is_sales = len(items) > 0 and "revenue" in items[0]

        if is_sales:
            # SALES METRICS
            total_revenue = sum(float(item.get("revenue", 0)) for item in items)
            total_qty_sold = sum(int(item.get("quantitySold", 0)) for item in items)
            avg_revenue = total_revenue / len(items) if items else 0

            # Count with promotions
            promo_sales = sum(
                1
                for item in items
                if item.get("promotionType") and item.get("promotionType") != "None"
            )

            metrics = [
                {
                    "label": "Total Revenue",
                    "value": total_revenue,
                    "format": "currency",
                    "icon": "💰",
                },
                {
                    "label": "Total Quantity Sold",
                    "value": total_qty_sold,
                    "format": "number",
                    "icon": "📦",
                },
                {
                    "label": "Average Sale Value",
                    "value": avg_revenue,
                    "format": "currency",
                    "icon": "📊",
                },
                {
                    "label": "Sales Count",
                    "value": len(items),
                    "format": "number",
                    "icon": "🧾",
                },
                {
                    "label": "Promotional Sales",
                    "value": promo_sales,
                    "format": "number",
                    "icon": "🏷️",
                },
            ]

            return {
                "display_type": "metrics",
                "data": {"metrics": metrics},
                "metadata": {"title": "Sales Metrics", "layout": "grid"},
            }

        # INVENTORY METRICS
        # Total value
        total_value = sum(
            float(item.get("sellingPrice", 0)) * float(item.get("quantity", 0))
            for item in items
        )

        # Low stock count
        low_stock = sum(
            1
            for item in items
            if float(item.get("quantity", 0)) < float(item.get("minQuantity", 0))
        )

        # Out of stock
        out_of_stock = sum(1 for item in items if float(item.get("quantity", 0)) == 0)

        # Average price
        prices = [
            float(item.get("sellingPrice", 0))
            for item in items
            if item.get("sellingPrice")
        ]
        avg_price = sum(prices) / len(prices) if prices else 0

        metrics = [
            {
                "label": "Total Items",
                "value": total_items,
                "format": "number",
                "icon": "📦",
            },
            {
                "label": "Total Inventory Value",
                "value": total_value,
                "format": "currency",
                "icon": "💰",
            },
            {
                "label": "Low Stock Items",
                "value": low_stock,
                "format": "number",
                "icon": "⚠️",
                "color": "warning" if low_stock > 0 else "success",
            },
            {
                "label": "Out of Stock",
                "value": out_of_stock,
                "format": "number",
                "icon": "🚫",
                "color": "danger" if out_of_stock > 0 else "success",
            },
            {
                "label": "Average Price",
                "value": avg_price,
                "format": "currency",
                "icon": "📊",
            },
        ]

        return {
            "display_type": "metrics",
            "data": {"metrics": metrics},
            "metadata": {"title": "Inventory Metrics", "layout": "grid"},
        }

    @staticmethod
    def _format_as_chart(items: List[Dict], query: str) -> Dict[str, Any]:
        """Format as chart data."""
        query_lower = query.lower()

        # Check if sales data
        is_sales = len(items) > 0 and "revenue" in items[0]

        if is_sales:
            # SALES CHARTS
            if "weather" in query_lower:
                # Revenue by Weather
                weather_revenue = {}
                for item in items:
                    weather = item.get("weatherCondition", "Unknown")
                    revenue = float(item.get("revenue", 0))
                    weather_revenue[weather] = weather_revenue.get(weather, 0) + revenue

                return {
                    "display_type": "chart",
                    "data": {
                        "chart_type": "bar",
                        "labels": list(weather_revenue.keys()),
                        "datasets": [
                            {
                                "label": "Revenue by Weather",
                                "data": list(weather_revenue.values()),
                                "backgroundColor": "#36A2EB",
                            }
                        ],
                    },
                    "metadata": {"title": "Revenue by Weather Condition"},
                }
            elif "promotion" in query_lower:
                # Revenue by Promotion
                promo_revenue = {}
                for item in items:
                    promo = item.get("promotionType", "None") or "None"
                    revenue = float(item.get("revenue", 0))
                    promo_revenue[promo] = promo_revenue.get(promo, 0) + revenue

                return {
                    "display_type": "chart",
                    "data": {
                        "chart_type": "pie",
                        "labels": list(promo_revenue.keys()),
                        "datasets": [
                            {
                                "label": "Revenue by Promotion",
                                "data": list(promo_revenue.values()),
                                "backgroundColor": [
                                    "#FF6384",
                                    "#36A2EB",
                                    "#FFCE56",
                                    "#4BC0C0",
                                    "#9966FF",
                                ],
                            }
                        ],
                    },
                    "metadata": {"title": "Revenue by Promotion Type"},
                }
            else:
                # Default: Revenue over Time (Line Chart)
                # Sort by date
                sorted_items = sorted(items, key=lambda x: x.get("saleDate", ""))
                dates = [item.get("saleDate") for item in sorted_items]
                revenues = [float(item.get("revenue", 0)) for item in sorted_items]

                return {
                    "display_type": "chart",
                    "data": {
                        "chart_type": "line",
                        "labels": dates,
                        "datasets": [
                            {
                                "label": "Revenue",
                                "data": revenues,
                                "borderColor": "#4BC0C0",
                                "fill": False,
                            }
                        ],
                    },
                    "metadata": {"title": "Revenue Trend"},
                }

        # INVENTORY CHARTS
        # Determine chart type based on query
        if (
            "by type" in query_lower
            or "by category" in query_lower
            or "distribution" in query_lower
        ):
            # Pie/Donut chart - distribution by type
            type_counts = {}
            for item in items:
                item_type = item.get("type", "Unknown")
                type_counts[item_type] = type_counts.get(item_type, 0) + 1

            return {
                "display_type": "chart",
                "data": {
                    "chart_type": "pie",
                    "labels": list(type_counts.keys()),
                    "datasets": [
                        {
                            "label": "Items by Type",
                            "data": list(type_counts.values()),
                            "backgroundColor": [
                                "#FF6384",
                                "#36A2EB",
                                "#FFCE56",
                                "#4BC0C0",
                                "#9966FF",
                                "#FF9F40",
                                "#FF6384",
                                "#C9CBCF",
                            ],
                        }
                    ],
                },
                "metadata": {
                    "title": "Inventory Distribution by Type",
                    "description": f"Showing {len(items)} items across {len(type_counts)} categories",
                },
            }

        elif "price" in query_lower or "cost" in query_lower:
            # Bar chart - price comparison
            sorted_items = sorted(
                items, key=lambda x: float(x.get("sellingPrice", 0)), reverse=True
            )[:10]

            return {
                "display_type": "chart",
                "data": {
                    "chart_type": "bar",
                    "labels": [
                        item.get("itemName", "Unknown") for item in sorted_items
                    ],
                    "datasets": [
                        {
                            "label": "Selling Price",
                            "data": [
                                float(item.get("sellingPrice", 0))
                                for item in sorted_items
                            ],
                            "backgroundColor": "#36A2EB",
                        }
                    ],
                },
                "metadata": {
                    "title": "Top 10 Items by Price",
                    "yAxisLabel": "Price ($)",
                },
            }

        elif "stock" in query_lower or "quantity" in query_lower:
            # Bar chart - stock levels
            sorted_items = sorted(items, key=lambda x: float(x.get("quantity", 0)))[:15]

            return {
                "display_type": "chart",
                "data": {
                    "chart_type": "bar",
                    "labels": [
                        item.get("itemName", "Unknown") for item in sorted_items
                    ],
                    "datasets": [
                        {
                            "label": "Current Stock",
                            "data": [
                                float(item.get("quantity", 0)) for item in sorted_items
                            ],
                            "backgroundColor": "#FF6384",
                        },
                        {
                            "label": "Min Stock",
                            "data": [
                                float(item.get("minQuantity", 0))
                                for item in sorted_items
                            ],
                            "backgroundColor": "#FFCE56",
                        },
                    ],
                },
                "metadata": {
                    "title": "Stock Levels (Lowest 15 Items)",
                    "yAxisLabel": "Quantity",
                },
            }

        # Default: pie chart by type
        return ResponseFormatter._format_as_chart(items, "distribution by type")

    @staticmethod
    def _format_as_table(items: List[Dict], query: str) -> Dict[str, Any]:
        """Format as data table."""
        if not items:
            return {
                "display_type": "text",
                "data": {"text": "No items to display"},
                "metadata": {},
            }

        # Determine which columns to show based on available data
        sample_item = items[0]

        # Define column configurations
        column_configs = {
            "id": {"label": "ID", "type": "text", "width": "80px"},
            "itemName": {
                "label": "Item Name",
                "type": "text",
                "width": "200px",
                "sortable": True,
            },
            "quantity": {
                "label": "Quantity",
                "type": "number",
                "width": "100px",
                "sortable": True,
            },
            "quantityUnit": {"label": "Unit", "type": "text", "width": "80px"},
            "type": {
                "label": "Type",
                "type": "text",
                "width": "120px",
                "filterable": True,
            },
            "supplier": {
                "label": "Supplier",
                "type": "text",
                "width": "150px",
                "filterable": True,
            },
            "costPrice": {
                "label": "Cost",
                "type": "currency",
                "width": "100px",
                "sortable": True,
            },
            "sellingPrice": {
                "label": "Price",
                "type": "currency",
                "width": "100px",
                "sortable": True,
            },
            "minQuantity": {"label": "Min Qty", "type": "number", "width": "90px"},
            "isActive": {"label": "Active", "type": "boolean", "width": "80px"},
            "lastRestockDate": {
                "label": "Last Restock",
                "type": "date",
                "width": "120px",
            },
            # Sales specific columns
            "saleDate": {
                "label": "Date",
                "type": "date",
                "width": "100px",
                "sortable": True,
            },
            "revenue": {
                "label": "Revenue",
                "type": "currency",
                "width": "100px",
                "sortable": True,
            },
            "quantitySold": {
                "label": "Qty Sold",
                "type": "number",
                "width": "80px",
                "sortable": True,
            },
            "weatherCondition": {"label": "Weather", "type": "text", "width": "100px"},
            "promotionType": {"label": "Promotion", "type": "text", "width": "120px"},
            "salesUid": {"label": "Sale ID", "type": "text", "width": "100px"},
        }

        # Select columns present in data
        columns = []
        for key in sample_item.keys():
            if key in column_configs:
                columns.append({"key": key, **column_configs[key]})

        # Format rows
        rows = []
        for item in items:
            row = {}
            for col in columns:
                key = col["key"]
                value = item.get(key)

                # Format based on type
                if col["type"] == "currency" and value is not None:
                    row[key] = {
                        "value": float(value),
                        "formatted": f"${float(value):.2f}",
                    }
                elif col["type"] == "number" and value is not None:
                    row[key] = {"value": float(value), "formatted": str(value)}
                elif col["type"] == "boolean":
                    row[key] = {
                        "value": bool(value),
                        "formatted": "✓" if value else "✗",
                    }
                elif col["type"] == "date" and value:
                    row[key] = {"value": value, "formatted": value}
                else:
                    row[key] = {
                        "value": value,
                        "formatted": str(value) if value else "",
                    }

            rows.append(row)

        return {
            "display_type": "table",
            "data": {"columns": columns, "rows": rows, "total_count": len(rows)},
            "metadata": {
                "title": f"Inventory Items ({len(rows)} items)",
                "searchable": True,
                "sortable": True,
                "exportable": True,
                "pagination": {"enabled": len(rows) > 10, "page_size": 10},
            },
        }

    @staticmethod
    def _format_as_list(items: List[Dict], query: str) -> Dict[str, Any]:
        """Format as simple list."""
        list_items = []

        for item in items:
            # Create a concise summary for each item
            title = item.get("itemName", "Unknown Item")
            subtitle = f"{item.get('quantity', 0)} {item.get('quantityUnit', 'units')}"

            details = []
            if item.get("type"):
                details.append(f"Type: {item['type']}")
            if item.get("supplier"):
                details.append(f"Supplier: {item['supplier']}")
            if item.get("sellingPrice"):
                details.append(f"Price: ${float(item['sellingPrice']):.2f}")

            # Status badge
            status = "active" if item.get("isActive", True) else "inactive"
            if float(item.get("quantity", 0)) == 0:
                status = "out_of_stock"
            elif float(item.get("quantity", 0)) < float(item.get("minQuantity", 0)):
                status = "low_stock"

            list_items.append(
                {
                    "id": item.get("id"),
                    "title": title,
                    "subtitle": subtitle,
                    "details": details,
                    "status": status,
                    "icon": "📦",
                }
            )

        return {
            "display_type": "list",
            "data": {"items": list_items},
            "metadata": {
                "title": f"Inventory Items ({len(list_items)})",
                "layout": "vertical",
            },
        }

    @staticmethod
    def _format_as_card(item: Dict, query: str) -> Dict[str, Any]:
        """Format single item as detailed card."""
        sections = []

        # Basic Info Section
        basic_info = {
            "title": "Basic Information",
            "fields": [
                {"label": "Item Name", "value": item.get("itemName", "N/A")},
                {"label": "Type", "value": item.get("type", "N/A")},
                {"label": "Description", "value": item.get("itemDescription", "N/A")},
            ],
        }
        sections.append(basic_info)

        # Stock Info Section
        stock_info = {
            "title": "Stock Information",
            "fields": [
                {
                    "label": "Current Quantity",
                    "value": f"{item.get('quantity', 0)} {item.get('quantityUnit', 'units')}",
                },
                {
                    "label": "Minimum Quantity",
                    "value": f"{item.get('minQuantity', 0)} {item.get('quantityUnit', 'units')}",
                },
                {
                    "label": "Auto Reorder",
                    "value": "Yes" if item.get("autoReorder") else "No",
                },
            ],
        }
        sections.append(stock_info)

        # Pricing Section
        if item.get("costPrice") or item.get("sellingPrice"):
            pricing_info = {
                "title": "Pricing",
                "fields": [
                    {
                        "label": "Cost Price",
                        "value": f"${float(item.get('costPrice', 0)):.2f}",
                    },
                    {
                        "label": "Selling Price",
                        "value": f"${float(item.get('sellingPrice', 0)):.2f}",
                    },
                ],
            }
            if item.get("costPrice") and item.get("sellingPrice"):
                margin = float(item["sellingPrice"]) - float(item["costPrice"])
                margin_pct = (
                    (margin / float(item["costPrice"])) * 100
                    if float(item["costPrice"]) > 0
                    else 0
                )
                pricing_info["fields"].append(
                    {"label": "Margin", "value": f"${margin:.2f} ({margin_pct:.1f}%)"}
                )
            sections.append(pricing_info)

        # Supplier Section
        if item.get("supplier"):
            supplier_info = {
                "title": "Supplier",
                "fields": [
                    {"label": "Supplier Name", "value": item.get("supplier", "N/A")},
                    {
                        "label": "Last Restock",
                        "value": item.get("lastRestockDate", "N/A"),
                    },
                ],
            }
            sections.append(supplier_info)

        return {
            "display_type": "card",
            "data": {
                "title": item.get("itemName", "Item Details"),
                "sections": sections,
            },
            "metadata": {
                "item_id": item.get("id"),
                "status": "active" if item.get("isActive") else "inactive",
            },
        }

    @staticmethod
    def _format_supplier_response(
        supplier_data: Dict, user_query: str
    ) -> Dict[str, Any]:
        """Format supplier data."""
        suppliers = [edge["node"] for edge in supplier_data.get("edges", [])]

        if not suppliers:
            return {
                "display_type": "text",
                "data": {"text": "No suppliers found."},
                "metadata": {},
            }

        # Format as table
        columns = [
            {
                "key": "supplierName",
                "label": "Supplier Name",
                "type": "text",
                "sortable": True,
            },
            {"key": "contactPerson", "label": "Contact Person", "type": "text"},
            {"key": "supplierEmail", "label": "Email", "type": "email"},
            {"key": "supplierPhone", "label": "Phone", "type": "phone"},
        ]

        rows = []
        for supplier in suppliers:
            row = {
                "supplierName": {
                    "value": supplier.get("supplierName"),
                    "formatted": supplier.get("supplierName", ""),
                },
                "contactPerson": {
                    "value": supplier.get("contactPerson"),
                    "formatted": supplier.get("contactPerson", ""),
                },
                "supplierEmail": {
                    "value": supplier.get("supplierEmail"),
                    "formatted": supplier.get("supplierEmail", ""),
                },
                "supplierPhone": {
                    "value": supplier.get("supplierPhone"),
                    "formatted": supplier.get("supplierPhone", ""),
                },
            }
            rows.append(row)

        return {
            "display_type": "table",
            "data": {"columns": columns, "rows": rows, "total_count": len(rows)},
            "metadata": {"title": "Suppliers", "searchable": True},
        }

    @staticmethod
    def _format_prediction_response(prediction_data: Dict) -> Dict[str, Any]:
        """Format prediction data for display."""
        product = prediction_data.get("product", "Unknown Product")
        forecast = prediction_data.get("forecast", [])
        disclaimer = prediction_data.get("disclaimer", "")

        # Format for Chart
        dates = []
        amounts = []
        quantities = []

        # Forecast structure: [{"date": "...", "predictions": [{"sales_amount": ...}]}]
        # Need to flatten if it's nested or handle direct list
        # Based on prediction_model/app.py: forecast is list of day_data
        # day_data = {"date": ..., "predictions": [...]}

        for day in forecast:
            date = day.get("date")
            preds = day.get("predictions", [])
            if preds:
                # Assuming single item prediction for now
                pred = preds[0]
                dates.append(date)
                amounts.append(pred.get("sales_amount", 0))
                quantities.append(pred.get("sales_quantity", 0))

        return {
            "display_type": "prediction",
            "data": {
                "product": product,
                "chart": {
                    "labels": dates,
                    "datasets": [
                        {
                            "label": "Predicted Revenue ($)",
                            "data": amounts,
                            "borderColor": "#8884d8",
                            "backgroundColor": "rgba(136, 132, 216, 0.2)",
                            "yAxisID": "y1",
                        },
                        {
                            "label": "Predicted Quantity",
                            "data": quantities,
                            "borderColor": "#82ca9d",
                            "backgroundColor": "rgba(130, 202, 157, 0.2)",
                            "yAxisID": "y2",
                        },
                    ],
                },
                "disclaimer": disclaimer,
            },
            "metadata": {
                "title": f"Sales Prediction: {product}",
                "subtitle": f"Next {len(dates)} Days",
            },
        }

    @staticmethod
    def _format_sales_report(
        report_data: List[Dict], user_query: str
    ) -> Dict[str, Any]:
        """Format aggregated sales report as chart or table."""
        if not report_data:
            return {
                "display_type": "text",
                "data": {"text": "No sales data available for report."},
                "metadata": {},
            }

        # Determine if grouping by product or date
        is_product = "name" in report_data[0]
        is_date = "date" in report_data[0]

        if is_product:
            # Bar chart for top products
            labels = [item.get("name", "Unknown") for item in report_data]
            revenues = [float(item.get("totalRevenue", 0)) for item in report_data]
            quantities = [float(item.get("totalQuantity", 0)) for item in report_data]

            return {
                "display_type": "chart",
                "data": {
                    "chart_type": "bar",
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "Total Revenue",
                            "data": revenues,
                            "backgroundColor": "#36A2EB",
                        },
                        {
                            "label": "Quantity Sold",
                            "data": quantities,
                            "backgroundColor": "#FF6384",
                        },
                    ],
                },
                "metadata": {"title": "Sales Report by Product"},
            }

        elif is_date:
            # Line chart for trends
            labels = [item.get("date", "") for item in report_data]
            revenues = [float(item.get("totalRevenue", 0)) for item in report_data]

            return {
                "display_type": "chart",
                "data": {
                    "chart_type": "line",
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "Total Revenue",
                            "data": revenues,
                            "borderColor": "#4BC0C0",
                            "fill": False,
                        }
                    ],
                },
                "metadata": {"title": "Sales Trend"},
            }

        return {
            "display_type": "text",
            "data": {"text": json.dumps(report_data, indent=2)},
            "metadata": {},
        }
