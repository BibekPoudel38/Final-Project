import graphene
from graphene_django.filter import DjangoFilterConnectionField
from .types import InventorType, SupplierType
from .filters import InventoryFilter, SupplierFilter

class Query(graphene.ObjectType):
    # 1. Single Item lookups (by global Relay ID)
    inventor_item = graphene.relay.Node.Field(InventorType)
    supplier = graphene.relay.Node.Field(SupplierType)

    # 2. List lookups with Advanced Filtering
    # The LLM can now query: all_inventory(minPrice: 10, itemName: "Widget")
    all_inventory = DjangoFilterConnectionField(InventorType, filterset_class=InventoryFilter)
    all_suppliers = DjangoFilterConnectionField(SupplierType, filterset_class=SupplierFilter)