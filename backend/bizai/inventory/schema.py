import graphene
from graphene_django.filter import DjangoFilterConnectionField
from .types import InventorType, SupplierType
from .filters import InventoryFilter, SupplierFilter


from .models import InventorModel, SupplierModel


class Query(graphene.ObjectType):
    # 1. Single Item lookups (by global Relay ID)
    inventor_item = graphene.relay.Node.Field(InventorType)
    supplier = graphene.relay.Node.Field(SupplierType)

    # 2. List lookups with Advanced Filtering
    # The LLM can now query: all_inventory(minPrice: 10, itemName: "Widget")
    all_inventory = DjangoFilterConnectionField(
        InventorType, filterset_class=InventoryFilter
    )
    all_suppliers = DjangoFilterConnectionField(
        SupplierType, filterset_class=SupplierFilter
    )

    def resolve_all_inventory(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return InventorModel.objects.none()
        return InventorModel.objects.filter(user=info.context.user, is_active=True)

    def resolve_all_suppliers(self, info, **kwargs):
        # Assuming suppliers are global or linked via some other logic, but if they should be private:
        # return SupplierModel.objects.filter(contact_address__merchant__user=info.context.user)
        # For now, leaving suppliers as is or if they are shared.
        # Checking models.py, SupplierModel doesn't seem to have a direct user link easily accessible without traversing Address.
        # Let's focus on Inventory for now.
        return SupplierModel.objects.all()
