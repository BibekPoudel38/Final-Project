from django.urls import path
from .views import (
    OnboardingView,
    ProfileView,
    POSConnectionView,
    EmployeeManagementView,
)

urlpatterns = [
    path("onboarding/", OnboardingView.as_view(), name="merchant-onboarding"),
    path("profile/", ProfileView.as_view(), name="merchant-profile"),
    path("pos/", POSConnectionView.as_view(), name="merchant-pos"),
    path("employees/", EmployeeManagementView.as_view(), name="employee-list-create"),
    path(
        "employees/<int:pk>/", EmployeeManagementView.as_view(), name="employee-delete"
    ),
]
