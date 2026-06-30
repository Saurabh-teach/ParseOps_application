from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    UserSerializer, RegisterSerializer, ChangePasswordSerializer, 
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    RegisterRequestSerializer, VerifyOTPSerializer, LoginSerializer,
    EmailSerializer, RequestEmailChangeSerializer, VerifyEmailChangeSerializer
)
from .otp_verify import OTPManager

User = get_user_model()


def _format_schedule_change_value(value):
    return value.strftime("%H:%M") if hasattr(value, "strftime") else str(value)


def _build_schedule_change_message(user, old_schedule, new_schedule):
    labels = {
        'work_start_time': 'Work start',
        'work_end_time': 'Work end',
        'lunch_break_start': 'Lunch start',
        'lunch_break_end': 'Lunch end',
        'tea_break_start': 'Tea start',
        'tea_break_end': 'Tea end',
    }
    changed = []
    for key, label in labels.items():
        if old_schedule.get(key) != new_schedule.get(key):
            changed.append(
                f"{label}: {_format_schedule_change_value(old_schedule.get(key))} -> "
                f"{_format_schedule_change_value(new_schedule.get(key))}"
            )

    user_name = user.get_full_name() or user.email
    return f"{user_name} updated their working schedule. " + "; ".join(changed)


def _notify_schedule_change_watchers(user, organization, old_schedule, new_schedule):
    from organizations.models import OrganizationMembership
    from tasks.models import Task
    from notifications.services import NotificationService

    recipient_ids = set(
        OrganizationMembership.objects.filter(
            organization=organization,
            role__in=['owner', 'admin'],
            is_active=True,
        ).values_list('user_id', flat=True)
    )
    recipient_ids.update(
        Task.objects.filter(
            organization=organization,
            assignee=user,
            is_deleted=False,
            created_by__isnull=False,
        )
        .exclude(status__in=['done', 'cancelled', 'archived'])
        .values_list('created_by_id', flat=True)
    )
    recipient_ids.discard(user.id)

    if not recipient_ids:
        return

    message = _build_schedule_change_message(user, old_schedule, new_schedule)
    for recipient in User.objects.filter(id__in=recipient_ids):
        NotificationService.send_notification(
            recipient=recipient,
            n_type='task_rescheduled',
            title='Member Schedule Changed',
            message=message,
            link=f"/members/{user.id}",
            organization=organization,
            data={
                'member_id': str(user.id),
                'old_schedule': {k: _format_schedule_change_value(v) for k, v in old_schedule.items()},
                'new_schedule': {k: _format_schedule_change_value(v) for k, v in new_schedule.items()},
            },
        )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=RegisterRequestSerializer)
    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            OTPManager.store_temp_data(email, serializer.validated_data)
            otp = OTPManager.generate_otp()
            OTPManager.store_otp(email, otp, purpose='registration')
            OTPManager.send_otp_email(email, otp, purpose_text="registration")
            
            return Response({
                "message": "OTP sent successfully",
                "email": OTPManager.mask_email(email)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyRegistrationOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=VerifyOTPSerializer)
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            is_valid, error_msg = OTPManager.verify_otp(email, otp, purpose='registration')
            if is_valid:
                data = OTPManager.get_temp_data(email)
                if not data:
                    return Response({"error": "Registration session expired. Please register again."}, status=status.HTTP_400_BAD_REQUEST)
                
                user = User.objects.create_user(
                    email=data['email'],
                    password=data['password']
                )
                
                try:
                    from notifications.organization import process_pending_invitations_for_new_user
                    process_pending_invitations_for_new_user(user)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error processing pending invitations: {e}")
                
                OTPManager.delete_otp(email, purpose='registration')
                cache.delete(f"temp_reg:{email}")
                
                return Response({"message": "Account created successfully! You can now login."}, status=status.HTTP_201_CREATED)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        from users.models import UserWorkingSchedule
        schedule, _ = UserWorkingSchedule.objects.get_or_create(user=instance)
        
        old_schedule = {
            'work_start_time': schedule.work_start_time,
            'work_end_time': schedule.work_end_time,
            'lunch_break_start': schedule.lunch_break_start,
            'lunch_break_end': schedule.lunch_break_end,
            'tea_break_start': schedule.tea_break_start,
            'tea_break_end': schedule.tea_break_end,
            'no_lunch_break': schedule.no_lunch_break,
            'no_tea_break': schedule.no_tea_break,
        }
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        updated_user = self.get_object()
        updated_schedule = updated_user.working_schedule
        
        new_schedule = {
            'work_start_time': updated_schedule.work_start_time,
            'work_end_time': updated_schedule.work_end_time,
            'lunch_break_start': updated_schedule.lunch_break_start,
            'lunch_break_end': updated_schedule.lunch_break_end,
            'tea_break_start': updated_schedule.tea_break_start,
            'tea_break_end': updated_schedule.tea_break_end,
        }

        shifted_count = 0
        if old_schedule != new_schedule:
            from tasks.services.scheduler import SchedulerService
            from organizations.models import OrganizationMembership
            from django.utils import timezone
            
            memberships = OrganizationMembership.objects.filter(
                user=updated_user,
                is_active=True
            ).select_related('organization')
            
            now = timezone.now()
            
            for membership in memberships:
                try:
                    rescheduled = SchedulerService.reschedule_from_datetime(
                        assignee_id=updated_user.id,
                        org_id=membership.organization.id,
                        from_datetime=now
                    )
                    shifted_count += len(rescheduled) if rescheduled else 0
                    _notify_schedule_change_watchers(
                        updated_user,
                        membership.organization,
                        old_schedule,
                        new_schedule,
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to reschedule tasks for user {updated_user.email} in org {membership.organization.name}: {e}")

        response_data = serializer.data
        response_data['rescheduled_tasks_count'] = shifted_count
        return Response(response_data)

class RequestEmailChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=RequestEmailChangeSerializer)
    def post(self, request):
        serializer = RequestEmailChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            password = serializer.validated_data['password']
            if not user.check_password(password):
                return Response({"error": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)
            
            new_email = serializer.validated_data['new_email']
            
            otp = OTPManager.generate_otp()
            OTPManager.store_otp(new_email, otp, purpose='email_change')
            OTPManager.send_otp_email(new_email, otp, purpose_text="email change")
            
            return Response({
                "message": "Verification OTP sent to your new email address.",
                "email": OTPManager.mask_email(new_email)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=VerifyEmailChangeSerializer)
    def post(self, request):
        serializer = VerifyEmailChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            new_email = serializer.validated_data['new_email']
            otp = serializer.validated_data['otp']
            
            is_valid, error_msg = OTPManager.verify_otp(new_email, otp, purpose='email_change')
            if is_valid:
                user.email = new_email
                user.save()
                
                OTPManager.delete_otp(new_email, purpose='email_change')
                
                return Response({"message": "Email updated successfully!"}, status=status.HTTP_200_OK)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.email = serializer.validated_data.get("email")
            user.set_password(serializer.validated_data.get("new_password"))
            
            was_temp = user.must_change_password
            user.must_change_password = False
            user.save()
            
            if was_temp:
                try:
                    from organizations.models import OrganizationMembership
                    from notifications.organization import create_temp_password_accepted_notification
                    memberships = OrganizationMembership.objects.filter(user=user, is_active=True)
                    for membership in memberships:
                        if membership.invited_by:
                            create_temp_password_accepted_notification(membership)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error triggering acceptance notification: {e}")
                    
            return Response({"status": "success", "message": "Email and Password updated successfully in database"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=PasswordResetConfirmSerializer)
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=PasswordResetRequestSerializer)
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            try:
                user = User.objects.get(email__iexact=email)
                user.set_password(password)
                user.save()
                return Response({"message": "Password updated successfully!"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            print(f"DEBUG LOGIN - Email received: '{email}', Password received: '{password}'")
            
            user = User.objects.filter(email__iexact=email).first()
            if not user or not user.check_password(password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            otp = OTPManager.generate_otp()
            OTPManager.store_otp(email, otp, purpose='login')
            OTPManager.send_otp_email(email, otp, purpose_text="login")
            
            return Response({
                "message": "OTP sent successfully",
                "email": OTPManager.mask_email(email)
            }, status=status.HTTP_200_OK)
            
        error_msg = "Authentication failed."
        if 'email' in serializer.errors:
            error_msg = serializer.errors['email'][0]
        elif 'password' in serializer.errors:
            error_msg = serializer.errors['password'][0]
            
        return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

class VerifyLoginOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=VerifyOTPSerializer)
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            is_valid, error_msg = OTPManager.verify_otp(email, otp, purpose='login')
            if is_valid:
                user = User.objects.filter(email__iexact=email).first()
                if not user:
                    return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                refresh = RefreshToken.for_user(user)
                
                OTPManager.delete_otp(email, purpose='login')
                
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "message": "Login successful",
                    "requires_password_change": getattr(user, 'must_change_password', False)
                }, status=status.HTTP_200_OK)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendRegistrationOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=EmailSerializer)
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            if not OTPManager.get_temp_data(email):
                return Response({"error": "No pending registration found for this email."}, status=status.HTTP_400_BAD_REQUEST)
            
            allowed, seconds = OTPManager.can_resend(email, purpose='registration')
            if not allowed:
                return Response({"error": f"Please wait {seconds} seconds before requesting a new OTP."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            otp = OTPManager.generate_otp()
            OTPManager.store_otp(email, otp, purpose='registration')
            OTPManager.send_otp_email(email, otp, purpose_text="registration")
            
            return Response({"message": "OTP resent successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendLoginOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=EmailSerializer)
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            if not User.objects.filter(email__iexact=email).exists():
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
            allowed, seconds = OTPManager.can_resend(email, purpose='login')
            if not allowed:
                return Response({"error": f"Please wait {seconds} seconds before requesting a new OTP."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            otp = OTPManager.generate_otp()
            OTPManager.store_otp(email, otp, purpose='login')
            OTPManager.send_otp_email(email, otp, purpose_text="login")
            
            return Response({"message": "OTP resent successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=EmailSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            if not User.objects.filter(email__iexact=email).exists():
                return Response({"error": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)

            can_send, timeLeft = OTPManager.can_resend(email, purpose='password_reset')
            if not can_send:
                return Response({"error": f"Please wait {timeLeft} seconds before requesting a new OTP."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            otp = OTPManager.generate_otp()
            OTPManager.store_otp(email, otp, purpose='password_reset')
            OTPManager.send_otp_email(email, otp, purpose_text="password reset")
            
            return Response({"message": "Password reset OTP sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=VerifyOTPSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = request.data.get('password') # We need the new password too

            if not new_password:
                return Response({"error": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)

            is_valid, error_msg = OTPManager.verify_otp(email, otp, purpose='password_reset')
            if not is_valid:
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email__iexact=email)
                user.set_password(new_password)
                
                was_temp = user.must_change_password
                user.must_change_password = False
                user.save()
                
                if was_temp:
                    try:
                        from organizations.models import OrganizationMembership
                        from notifications.organization import create_temp_password_accepted_notification
                        memberships = OrganizationMembership.objects.filter(user=user, is_active=True)
                        for membership in memberships:
                            if membership.invited_by:
                                create_temp_password_accepted_notification(membership)
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Error triggering acceptance notification from reset password: {e}")
                
                OTPManager.delete_otp(email, purpose='password_reset')
                
                return Response({"message": "Password updated successfully! You can now login."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User no longer exists."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
import urllib.parse
import requests

class MicrosoftLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        client_id = getattr(settings, "MICROSOFT_CLIENT_ID", "")
        client_secret = getattr(settings, "MICROSOFT_CLIENT_SECRET", "")
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        
        is_configured = (
            client_id and 
            "mock" not in client_id.lower() and 
            "your_real" not in client_id.lower() and 
            client_secret and 
            "mock" not in client_secret.lower() and 
            "your_real" not in client_secret.lower()
        )
        
        if not is_configured:
            mock_url = reverse("microsoft-mock-login")
            state = request.GET.get("state", "oauth-state")
            return HttpResponseRedirect(f"{mock_url}?state={state}")
            
        redirect_uri = settings.MICROSOFT_REDIRECT_URI
        scope = "openid profile email"
        state = request.GET.get("state", "oauth-state")
        
        microsoft_auth_url = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            f"?client_id={client_id}"
            "&response_type=code"
            f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
            f"&scope={urllib.parse.quote(scope)}"
            f"&state={state}"
            "&response_mode=query"
        )
        return HttpResponseRedirect(microsoft_auth_url)


class MicrosoftCallbackView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        
        if not code:
            return HttpResponseRedirect(f"{frontend_url}/?error=no_code_provided")
            
        email = None
        first_name = "Microsoft"
        last_name = "User"

        if getattr(settings, "MICROSOFT_MOCK", True):
            email = request.GET.get("email", "microsoft_developer@acme.com")
            first_name = request.GET.get("first_name", "Microsoft")
            last_name = request.GET.get("last_name", "Developer")
        else:
            try:
                token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
                payload = {
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
                    "grant_type": "authorization_code",
                }
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                token_res = requests.post(token_url, data=payload, headers=headers).json()
                
                access_token = token_res.get("access_token")
                if not access_token:
                    return HttpResponseRedirect(f"{frontend_url}/?error=token_exchange_failed")
                
                graph_url = "https://graph.microsoft.com/v1.0/me"
                graph_headers = {"Authorization": f"Bearer {access_token}"}
                profile = requests.get(graph_url, headers=graph_headers).json()
                
                email = profile.get("mail") or profile.get("userPrincipalName")
                first_name = profile.get("givenName", "Microsoft")
                last_name = profile.get("surname", "User")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Microsoft OAuth Error: {e}")
                return HttpResponseRedirect(f"{frontend_url}/?error=microsoft_auth_exception")

        if not email:
            return HttpResponseRedirect(f"{frontend_url}/?error=failed_to_retrieve_email")

        user, created = User.objects.get_or_create(
            email=email.lower(),
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "must_change_password": False,
            }
        )
        if created:
            user.set_unusable_password()
            user.save()
            
        try:
            from organizations.models import Organization, OrganizationMembership
            org = Organization.objects.filter(name='TestWorkspaceSSO').first()
            if not org:
                org = Organization.objects.first()
            if org:
                membership, created = OrganizationMembership.objects.get_or_create(
                    organization=org,
                    user=user,
                    defaults={"role": "owner"}
                )
                if not created:
                    membership.role = "owner"
                    membership.save()
        except Exception:
            pass

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        return HttpResponseRedirect(f"{frontend_url}/?access={access_token}&refresh={refresh_token}")


class MicrosoftMockLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        state = request.GET.get("state", "")
        callback_url = reverse("microsoft-callback")
        full_callback = request.build_absolute_uri(callback_url)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simulated Microsoft Sign-in</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {{
                    --primary: #0067b8;
                    --primary-hover: #005da6;
                    --bg-page: #f2f2f2;
                    --bg-card: #ffffff;
                    --text-main: #1b1b1b;
                    --text-muted: #555555;
                    --border: #8a8a8a;
                    --warning-bg: #fff8eb;
                    --warning-border: #ffb900;
                    --warning-text: #6b3e00;
                }}
                @media (prefers-color-scheme: dark) {{
                    :root {{
                        --bg-page: #0f172a;
                        --bg-card: #1e293b;
                        --text-main: #f8fafc;
                        --text-muted: #cbd5e1;
                        --border: #475569;
                        --warning-bg: #1e1b12;
                        --warning-border: #b45309;
                        --warning-text: #fde047;
                        --primary: #3b82f6;
                        --primary-hover: #2563eb;
                    }}
                }}
                body {{
                    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
                    background: var(--bg-page);
                    color: var(--text-main);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 1.5rem;
                    box-sizing: border-box;
                }}
                .card {{
                    background: var(--bg-card);
                    border: 1px solid var(--border);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 440px;
                    padding: 44px;
                    box-sizing: border-box;
                    border-radius: 4px;
                }}
                .logo-container {{
                    margin-bottom: 24px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                .logo-text {{
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: var(--text-muted);
                }}
                h1 {{
                    font-size: 1.5rem;
                    font-weight: 600;
                    margin: 0 0 16px 0;
                }}
                .notice {{
                    background: var(--warning-bg);
                    border-left: 4px solid var(--warning-border);
                    color: var(--warning-text);
                    padding: 12px 16px;
                    margin-bottom: 24px;
                    font-size: 0.875rem;
                    border-radius: 4px;
                    line-height: 1.5;
                }}
                .notice-title {{
                    font-weight: bold;
                    margin-bottom: 4px;
                }}
                .form-group {{
                    margin-bottom: 18px;
                }}
                label {{
                    display: block;
                    font-size: 0.8125rem;
                    margin-bottom: 6px;
                    font-weight: 500;
                }}
                input[type="text"], input[type="email"] {{
                    width: 100%;
                    padding: 8px 10px;
                    border: 1px solid var(--border);
                    background: transparent;
                    color: var(--text-main);
                    font-size: 0.9375rem;
                    border-radius: 2px;
                    box-sizing: border-box;
                    outline: none;
                    transition: border-color 0.2s;
                }}
                input[type="text"]:focus, input[type="email"]:focus {{
                    border-color: var(--primary);
                }}
                .button-group {{
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                    margin-top: 28px;
                }}
                .btn {{
                    font-size: 0.9375rem;
                    padding: 6px 20px;
                    border-radius: 2px;
                    cursor: pointer;
                    font-weight: 400;
                    border: none;
                    transition: background 0.2s;
                }}
                .btn-primary {{
                    background: var(--primary);
                    color: #ffffff;
                }}
                .btn-primary:hover {{
                    background: var(--primary-hover);
                }}
                .btn-secondary {{
                    background: #cccccc;
                    color: #000000;
                }}
                .btn-secondary:hover {{
                    background: #bbbbbb;
                }}
                @media(prefers-color-scheme: dark) {{
                    .btn-secondary {{
                        background: #475569;
                        color: #ffffff;
                    }}
                    .btn-secondary:hover {{
                        background: #334155;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="logo-container">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 23 23">
                        <path fill="#f35325" d="M0 0h11v11H0z"/>
                        <path fill="#81bc06" d="M12 0h11v11H12z"/>
                        <path fill="#05a6f0" d="M0 12h11v11H0z"/>
                        <path fill="#ffba08" d="M12 12h11v11H12z"/>
                    </svg>
                    <span class="logo-text">Microsoft</span>
                </div>
                
                <h1>Sign in (Mock AD)</h1>
                
                <div class="notice">
                    <div class="notice-title">💡 Developer Simulation Mode</div>
                    ParseOps is running in development mode. Real Microsoft account credentials are <strong>not required</strong>. You can enter any mock details below to simulate a successful login.
                </div>
                
                <form method="GET" action="{full_callback}">
                    <input type="hidden" name="code" value="mock-auth-code-12345"/>
                    <input type="hidden" name="state" value="{state}"/>
                    
                    <div class="form-group">
                        <label for="email">Email address</label>
                        <input type="email" id="email" name="email" value="microsoft_developer@acme.com" required autocomplete="email" />
                    </div>
                    
                    <div class="form-group">
                        <label for="first_name">First Name</label>
                        <input type="text" id="first_name" name="first_name" value="Microsoft" required autocomplete="given-name" />
                    </div>
                    
                    <div class="form-group">
                        <label for="last_name">Last Name</label>
                        <input type="text" id="last_name" name="last_name" value="Developer" required autocomplete="family-name" />
                    </div>
                    
                    <div class="button-group">
                        <button type="button" class="btn btn-secondary" onclick="window.location.href='{frontend_url}'">Cancel</button>
                        <button type="submit" class="btn btn-primary">Sign in</button>
                    </div>
                </form>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content)


class MicrosoftOAuthView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email", "microsoft_developer@acme.com")
        first_name = request.data.get("first_name", "Microsoft")
        last_name = request.data.get("last_name", "Developer")

        user, created = User.objects.get_or_create(
            email=email.lower(),
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "must_change_password": False,
            }
        )
        if created:
            user.set_unusable_password()
            user.save()
            
        try:
            from organizations.models import Organization, OrganizationMembership
            org = Organization.objects.filter(name='TestWorkspaceSSO').first()
            if not org:
                org = Organization.objects.first()
            if org:
                membership, created = OrganizationMembership.objects.get_or_create(
                    organization=org,
                    user=user,
                    defaults={"role": "owner"}
                )
                if not created:
                    membership.role = "owner"
                    membership.save()
        except Exception:
            pass

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "Login successful",
            "requires_password_change": False
        }, status=status.HTTP_200_OK)


from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import LeaveRequest
from .serializers import LeaveRequestSerializer
from organizations.models import OrganizationMembership, Organization

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action in ['approve', 'reject', 'retrieve']:
            return LeaveRequest.objects.all()
        org_id = self.request.query_params.get('organization')
        qs = LeaveRequest.objects.filter(user=self.request.user)
        if org_id:
            qs = qs.filter(organization_id=org_id)
        return qs

    def perform_create(self, serializer):
        leave_request = serializer.save(user=self.request.user)
        org = leave_request.organization
        
        if org and leave_request.leave_type not in ['Unpaid', 'Maternity_Paternity', 'WFH']:
            from .models import LeaveBalance
            balance, _ = LeaveBalance.objects.get_or_create(
                user=self.request.user,
                organization=org,
                leave_type=leave_request.leave_type,
                defaults={'total_days': 10.0, 'used_days': 0.0}
            )
            balance.used_days += leave_request.number_of_days
            balance.save()

        if org:
            from tasks.services import NotificationService
            managers = OrganizationMembership.objects.filter(
                organization=org,
                role__in=['owner', 'admin'],
                is_active=True
            ).select_related('user')
            
            applicant_name = f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.email
            for mgr in managers:
                if mgr.user != self.request.user:
                    NotificationService.send_notification(
                        recipient=mgr.user,
                        n_type='info',
                        title='New Leave Request Submitted',
                        message=f"{applicant_name} has requested leave from {leave_request.start_date} to {leave_request.end_date}.",
                        organization=org
                    )

    @action(detail=False, methods=['get'], url_path='all')
    def list_all(self, request):
        org_id = request.query_params.get('organization')
        if not org_id:
            return Response({"error": "organization parameter is required."}, status=400)
            
        org = get_object_or_404(Organization, id=org_id)
        
        membership = OrganizationMembership.objects.filter(organization=org, user=request.user, is_active=True).first()
        if not membership or membership.role not in ['owner', 'admin']:
            return Response({"error": "Only Admins or Owners can view all leave requests."}, status=403)
            
        qs = LeaveRequest.objects.filter(organization=org).select_related('user', 'approved_by')
        
        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
            
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        org = leave_request.organization
        
        membership = OrganizationMembership.objects.filter(organization=org, user=request.user, is_active=True).first()
        if not membership or membership.role not in ['owner', 'admin']:
            return Response({"error": "Only Admins or Owners can approve leave requests."}, status=403)
            
        leave_request.status = 'Approved'
        leave_request.approved_by = request.user
        leave_request.save()
        
        from tasks.services import NotificationService
        NotificationService.send_notification(
            recipient=leave_request.user,
            n_type='info',
            title='Leave Request Approved',
            message=f"Your leave request for {leave_request.start_date} to {leave_request.end_date} has been approved by {request.user.first_name}.",
            organization=org
        )
        
        return Response(self.get_serializer(leave_request).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        org = leave_request.organization
        
        membership = OrganizationMembership.objects.filter(organization=org, user=request.user, is_active=True).first()
        if not membership or membership.role not in ['owner', 'admin']:
            return Response({"error": "Only Admins or Owners can reject leave requests."}, status=403)
            
        rejection_reason = request.data.get('reason', '')
        leave_request.status = 'Rejected'
        leave_request.approved_by = request.user
        leave_request.rejection_reason = rejection_reason
        leave_request.save()
        
        if org and leave_request.leave_type not in ['Unpaid', 'Maternity_Paternity', 'WFH']:
            from .models import LeaveBalance
            try:
                balance = LeaveBalance.objects.get(user=leave_request.user, organization=org, leave_type=leave_request.leave_type)
                balance.used_days -= leave_request.number_of_days
                balance.save()
            except LeaveBalance.DoesNotExist:
                pass

        from tasks.services import NotificationService
        NotificationService.send_notification(
            recipient=leave_request.user,
            n_type='info',
            title='Leave Request Rejected',
            message=f"Your leave request for {leave_request.start_date} to {leave_request.end_date} has been rejected by {request.user.first_name}. Reason: {rejection_reason}",
            organization=org
        )
        
        return Response(self.get_serializer(leave_request).data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        leave_request = self.get_object()
        org = leave_request.organization
        
        if leave_request.user != request.user:
            return Response({"error": "You can only cancel your own leave requests."}, status=403)
            
        cancellation_reason = request.data.get('reason', '')
        leave_request.status = 'Cancelled'
        leave_request.cancellation_reason = cancellation_reason
        leave_request.save()
        
        if org and leave_request.leave_type not in ['Unpaid', 'Maternity_Paternity', 'WFH']:
            from .models import LeaveBalance
            try:
                balance = LeaveBalance.objects.get(user=leave_request.user, organization=org, leave_type=leave_request.leave_type)
                balance.used_days -= leave_request.number_of_days
                balance.save()
            except LeaveBalance.DoesNotExist:
                pass
                
        if org:
            from tasks.services import NotificationService
            managers = OrganizationMembership.objects.filter(
                organization=org,
                role__in=['owner', 'admin'],
                is_active=True
            ).select_related('user')
            
            applicant_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
            for mgr in managers:
                NotificationService.send_notification(
                    recipient=mgr.user,
                    n_type='info',
                    title='Leave Request Cancelled',
                    message=f"{applicant_name} has cancelled their leave from {leave_request.start_date} to {leave_request.end_date}. Reason: {cancellation_reason}",
                    organization=org
                )

        return Response(self.get_serializer(leave_request).data)

from .models import LeaveBalance
from .serializers import LeaveBalanceSerializer

class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        org_id = self.request.query_params.get('organization')
        qs = LeaveBalance.objects.filter(user=self.request.user)
        if org_id:
            qs = qs.filter(organization_id=org_id)
        return qs



