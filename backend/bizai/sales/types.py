import graphene
from graphene_django import DjangoObjectType
from .models import SalesModel, SalesHolidayModel


class SalesHolidayType(DjangoObjectType):
    class Meta:
        model = SalesHolidayModel
        fields = "__all__"
        interfaces = (graphene.relay.Node,)


class SalesType(DjangoObjectType):
    class Meta:
        model = SalesModel
        fields = "__all__"
        interfaces = (graphene.relay.Node,)

    # Computed fields for convenience
    revenue_per_unit = graphene.Float()

    def resolve_revenue_per_unit(self, info):
        if self.quantity_sold and self.revenue:
            return float(self.revenue) / float(self.quantity_sold)
        return 0.0


class SalesReportItemType(graphene.ObjectType):
    name = graphene.String()
    total_revenue = graphene.Float()
    total_quantity = graphene.Float()
    date = graphene.String()
