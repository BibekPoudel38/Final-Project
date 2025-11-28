import django_filters
from django.db.models import F, Q
from .models import InventorModel, SupplierModel


class InventoryFilter(django_filters.FilterSet):
    # Text search (Case insensitive contains)
    item_name = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(
        field_name="item_description", lookup_expr="icontains"
    )
    supplier_name = django_filters.CharFilter(
        field_name="supplier", lookup_expr="icontains"
    )
    item_location = django_filters.CharFilter(
        field_name="item_location", lookup_expr="icontains"
    )
    user_email = django_filters.CharFilter(method="filter_by_email")

    # Numeric Ranges
    min_price = django_filters.NumberFilter(
        field_name="selling_price", lookup_expr="gte"
    )
    max_price = django_filters.NumberFilter(
        field_name="selling_price", lookup_expr="lte"
    )
    min_quantity = django_filters.NumberFilter(field_name="quantity", lookup_expr="gte")
    max_quantity = django_filters.NumberFilter(field_name="quantity", lookup_expr="lte")
    cost_price_range = django_filters.RangeFilter(field_name="cost_price")
    selling_price_range = django_filters.RangeFilter(field_name="selling_price")
    min_margin_price_range = django_filters.RangeFilter(field_name="min_margin_price")

    # Date Ranges
    restocked_after = django_filters.DateFilter(
        field_name="last_restock_date", lookup_expr="gte"
    )
    restocked_before = django_filters.DateFilter(
        field_name="last_restock_date", lookup_expr="lte"
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    updated_after = django_filters.DateTimeFilter(
        field_name="updated_at", lookup_expr="gte"
    )
    updated_before = django_filters.DateTimeFilter(
        field_name="updated_at", lookup_expr="lte"
    )

    # Boolean flags for quick status checks
    is_out_of_stock = django_filters.BooleanFilter(method="filter_is_out_of_stock")
    may_require_order = django_filters.BooleanFilter(method="filter_may_require_order")
    has_image = django_filters.BooleanFilter(method="filter_has_image")
    has_supplier = django_filters.BooleanFilter(method="filter_has_supplier")

    # Ordering
    order_by = django_filters.OrderingFilter(
        fields=(
            ("item_name", "item_name"),
            ("quantity", "quantity"),
            ("selling_price", "selling_price"),
            ("last_restock_date", "last_restock_date"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        )
    )

    class Meta:
        model = InventorModel
        fields = ["is_active", "auto_reorder", "type", "business", "quantity_unit"]

    def filter_by_email(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(user__email__iexact=value)
            | Q(business__business_email__iexact=value)
            | Q(business__owner__email__iexact=value)
        )

    def filter_is_out_of_stock(self, queryset, name, value):
        if value is not None:
            return (
                queryset.filter(quantity__lte=0)
                if value
                else queryset.filter(quantity__gt=0)
            )
        return queryset

    def filter_may_require_order(self, queryset, name, value):
        if value is not None:
            return (
                queryset.filter(quantity__lte=F("min_quantity"))
                if value
                else queryset.filter(quantity__gt=F("min_quantity"))
            )
        return queryset

    def filter_has_image(self, queryset, name, value):
        if value is not None:
            return (
                queryset.exclude(image__isnull=True).exclude(image__exact="")
                if value
                else queryset.filter(image__isnull=True)
                | queryset.filter(image__exact="")
            )
        return queryset

    def filter_has_supplier(self, queryset, name, value):
        if value is not None:
            return (
                queryset.exclude(supplier__isnull=True).exclude(supplier__exact="")
                if value
                else queryset.filter(supplier__isnull=True)
                | queryset.filter(supplier__exact="")
            )
        return queryset


class SupplierFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="supplier_name", lookup_expr="icontains"
    )
    email = django_filters.CharFilter(
        field_name="supplier_email", lookup_expr="icontains"
    )
    order_by = django_filters.OrderingFilter(
        fields=(
            ("supplier_name", "supplier_name"),
            ("contact_person", "contact_person"),
        )
    )

    class Meta:
        model = SupplierModel
        fields = ["contact_person"]
