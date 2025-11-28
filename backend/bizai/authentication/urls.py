from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="Login View"),
    path("signup/", views.SignupView.as_view(), name="Signup View"),
    # path("logout/", logout, name="Logout View"),
    #     path('generate_otp/', views.generateOtp, name="OTP Generator View"),
    #     path('validate_otp/', views.validate_Otp, name="Validate OTP Code"),
    #     path('reset_password/', views.ResetPassword.as_view(), name="Reset password"),
    # Supabase handles token issuance. Frontend should call Supabase auth directly.
    path("profile/", views.ProfileView.as_view(), name="Profile View"),
    path(
        "profile/update/", views.ProfileUpdateView.as_view(), name="Profile Update View"
    ),
    path("change_password/", views.ChangePassword.as_view(), name="Change Password"),
    path("checkemail/", views.send_reset_password_otp, name="Send Reset Password OTP"),
    path("verifyotp/", views.verify_reset_password_otp, name="Validate OTP Code"),
    path("resetpassword/", views.reset_password, name="Reset Password"),
    path("google/", views.GoogleLoginAPIView.as_view(), name="google-login"),
]
