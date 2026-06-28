from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, RegisterView, LogoutView, 
    UserProfileView, ChangePasswordView, PasswordResetRequestView,
    PasswordResetConfirmView, VerifyRegistrationOTPView, LoginView,
    VerifyLoginOTPView, ResendRegistrationOTPView, ResendLoginOTPView,
    ForgotPasswordView, ResetPasswordVerifyView, RequestEmailChangeView,
    VerifyEmailChangeView,
    MicrosoftLoginView, MicrosoftCallbackView, MicrosoftMockLoginView, MicrosoftOAuthView,
    LeaveRequestViewSet, LeaveBalanceViewSet
)

router = DefaultRouter()
router.register(r"list", UserViewSet, basename="user")
router.register(r"leaves", LeaveRequestViewSet, basename="leave")
router.register(r"leave-balances", LeaveBalanceViewSet, basename="leave-balance")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-registration-otp/", VerifyRegistrationOTPView.as_view(), name="verify-registration-otp"),
    path("login/", LoginView.as_view(), name="login"),
    path("verify-login-otp/", VerifyLoginOTPView.as_view(), name="verify-login-otp"),
    path("resend-registration-otp/", ResendRegistrationOTPView.as_view(), name="resend-registration-otp"),

    path("resend-login-otp/", ResendLoginOTPView.as_view(), name="resend-login-otp"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password-verify/", ResetPasswordVerifyView.as_view(), name="reset-password-verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("request-email-change/", RequestEmailChangeView.as_view(), name="request-email-change"),
    path("verify-email-change/", VerifyEmailChangeView.as_view(), name="verify-email-change"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("reset-password/", PasswordResetRequestView.as_view(), name="reset-password"),
    path("reset-password-confirm/", PasswordResetConfirmView.as_view(), name="reset-password-confirm"),
    
    # Microsoft OAuth
    path("auth/microsoft/login/", MicrosoftLoginView.as_view(), name="microsoft-login"),
    path("auth/microsoft/callback/", MicrosoftCallbackView.as_view(), name="microsoft-callback"),
    path("auth/microsoft/mock/", MicrosoftMockLoginView.as_view(), name="microsoft-mock-login"),
    path("auth/microsoft/", MicrosoftOAuthView.as_view(), name="microsoft-oauth-fallback"),

    path("", include(router.urls)),
]