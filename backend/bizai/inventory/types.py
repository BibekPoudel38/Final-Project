import graphene
from graphene_django import DjangoObjectType
from .models import InventorModel, SupplierModel

class InventorType(DjangoObjectType):
    class Meta:
        model = InventorModel
        # Expose these fields to the API
        fields = "__all__" 
        # Use Relay for standard pagination
        interfaces = (graphene.relay.Node, )

    # Computed field example (LLMs love summarized data)
    profit_margin = graphene.Float()

    def resolve_profit_margin(self, info):
        if self.selling_price and self.cost_price:
            return self.selling_price - self.cost_price
        return 0.0

class SupplierType(DjangoObjectType):
    class Meta:
        model = SupplierModel
        fields = "__all__"
        interfaces = (graphene.relay.Node, )