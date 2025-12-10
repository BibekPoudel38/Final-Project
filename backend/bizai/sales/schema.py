import graphene
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Sum, Q
from .types import SalesType, SalesHolidayType, SalesReportItemType
from .filters import SalesFilter, SalesHolidayFilter
from .models import SalesModel


class Query(graphene.ObjectType):
    sales_item = graphene.relay.Node.Field(SalesType)
    sales_holiday = graphene.relay.Node.Field(SalesHolidayType)

    all_sales = DjangoFilterConnectionField(SalesType, filterset_class=SalesFilter)
    all_sales_holidays = DjangoFilterConnectionField(
        SalesHolidayType, filterset_class=SalesHolidayFilter
    )

    # Aggregation Query
    sales_report = graphene.List(
        SalesReportItemType,
        group_by=graphene.String(default_value="product"),  # product, date
        date_from=graphene.String(),
        date_to=graphene.String(),
        user_email=graphene.String(),
    )

    def resolve_all_sales(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return SalesModel.objects.none()
        return SalesModel.objects.filter(
            prod_id__user=info.context.user, is_active=True
        )

    def resolve_sales_report(
        self, info, group_by, date_from=None, date_to=None, user_email=None
    ):
        # Enforce authentication
        if not info.context.user.is_authenticated:
            return []

        # Filter by the logged-in user, ignoring the user_email argument if passed
        queryset = SalesModel.objects.filter(
            prod_id__user=info.context.user, is_active=True
        )

        if date_from:
            queryset = queryset.filter(sale_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(sale_date__lte=date_to)

        if group_by == "product":
            data = (
                queryset.values("prod_id__item_name")
                .annotate(
                    total_revenue=Sum("revenue"), total_quantity=Sum("quantity_sold")
                )
                .order_by("-total_revenue")
            )

            return [
                SalesReportItemType(
                    name=item["prod_id__item_name"],
                    total_revenue=item["total_revenue"],
                    total_quantity=item["total_quantity"],
                )
                for item in data
            ]

        elif group_by == "date":
            data = (
                queryset.values("sale_date")
                .annotate(
                    total_revenue=Sum("revenue"), total_quantity=Sum("quantity_sold")
                )
                .order_by("sale_date")
            )

            return [
                SalesReportItemType(
                    date=item["sale_date"].strftime("%Y-%m-%d"),
                    total_revenue=item["total_revenue"],
                    total_quantity=item["total_quantity"],
                )
                for item in data
            ]

        return []
