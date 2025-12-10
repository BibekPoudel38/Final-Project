from django.urls import path
from .views import (
    InventoryDashboardView,
    InventoryCategoryView,
    InventoryListView,
    InventoryExportView,
    InventoryImportView,
    InventoryCreateView,
    InventoryDetailView,
    InventoryItemAnalyticsView,
    InventoryUpdateView,
)

urlpatterns = [
    path("dashboard/", InventoryDashboardView.as_view(), name="inventory-dashboard"),
    path(
        "category-breakdown/",
        InventoryCategoryView.as_view(),
        name="inventory-category",
    ),
    path("list/", InventoryListView.as_view(), name="inventory-list"),
    path("create/", InventoryCreateView.as_view(), name="inventory-create"),
    path("export/", InventoryExportView.as_view(), name="inventory-export"),
    path("import/", InventoryImportView.as_view(), name="inventory-import"),
    path("<int:pk>/", InventoryDetailView.as_view(), name="inventory-detail"),
    path("<int:pk>/update/", InventoryUpdateView.as_view(), name="inventory-update"),
    path(
        "<int:pk>/analytics/",
        InventoryItemAnalyticsView.as_view(),
        name="inventory-item-analytics",
    ),
]
