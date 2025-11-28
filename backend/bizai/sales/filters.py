import django_filters
from django.db.models import Q
from .models import SalesModel, SalesHolidayModel


class SalesHolidayFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    date_range = django_filters.DateFromToRangeFilter(field_name="date")

    class Meta:
        model = SalesHolidayModel
        fields = ["name", "date"]


class SalesFilter(django_filters.FilterSet):
    # Text Search
    sales_uid = django_filters.CharFilter(lookup_expr="icontains")
    weather_condition = django_filters.CharFilter(lookup_expr="icontains")
    promotion_type = django_filters.CharFilter(lookup_expr="icontains")
    user_email = django_filters.CharFilter(method="filter_by_email")

    def filter_by_email(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(prod_id__user__email__iexact=value)
            | Q(prod_id__business__business_email__iexact=value)
            | Q(prod_id__business__owner__email__iexact=value)
        )

    # Product Search
    product_name = django_filters.CharFilter(
        field_name="prod_id__item_name", lookup_expr="icontains"
    )

    # Numeric Ranges
    min_quantity = django_filters.NumberFilter(
        field_name="quantity_sold", lookup_expr="gte"
    )
    max_quantity = django_filters.NumberFilter(
        field_name="quantity_sold", lookup_expr="lte"
    )
    min_revenue = django_filters.NumberFilter(field_name="revenue", lookup_expr="gte")
    max_revenue = django_filters.NumberFilter(field_name="revenue", lookup_expr="lte")
    min_temperature = django_filters.NumberFilter(
        field_name="weather_temperature", lookup_expr="gte"
    )
    max_temperature = django_filters.NumberFilter(
        field_name="weather_temperature", lookup_expr="lte"
    )

    # Date Ranges
    sale_date_after = django_filters.DateFilter(
        field_name="sale_date", lookup_expr="gte"
    )
    sale_date_before = django_filters.DateFilter(
        field_name="sale_date", lookup_expr="lte"
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    # Ordering
    order_by = django_filters.OrderingFilter(
        fields=(
            ("sale_date", "sale_date"),
            ("revenue", "revenue"),
            ("quantity_sold", "quantity_sold"),
            ("created_at", "created_at"),
        )
    )

    class Meta:
        model = SalesModel
        fields = ["was_on_sale", "is_active", "prod_id"]
