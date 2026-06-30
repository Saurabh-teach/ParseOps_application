import random
import logging
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

class OTPManager:
    
    @staticmethod
    def generate_otp():
        """Generates a secure 6-digit numeric OTP."""
        return str(random.randint(100000, 999999))

    @staticmethod
    def store_otp(email, otp, purpose='auth', timeout=300):
        email = email.lower() 
        key = f"otp:{purpose}:{email}"
        print(f"DEBUG: Storing OTP {otp} for {email} with key {key}") 
        try:
            cache.set(key, otp, timeout=timeout)
            import os
            try:
                debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'otp_debug.txt')
                with open(debug_path, 'w') as f:
                    f.write(otp)
                print("DEBUG: Wrote OTP to", debug_path)
            except Exception as fe:
                print("Failed to write otp_debug.txt:", fe)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
        return key

    @staticmethod
    def verify_otp(email, otp, purpose='auth'):
        email = email.lower() 
        key = f"otp:{purpose}:{email}"
        attempts_key = f"attempts:{purpose}:{email}"
        
        stored_otp = cache.get(key)
        print(f"DEBUG: Verifying OTP for {email}. Key: {key}, Stored: {stored_otp}, Provided: {otp}") 
        
        if not stored_otp:
            return False, "OTP has expired or was never requested. Please request a new one."

        attempts = cache.get(attempts_key) or 0
        if attempts >= 3:
            return False, "Too many attempts. Please request a new OTP."
            
        if str(stored_otp) == str(otp):
            try:
                cache.delete(key)
                cache.delete(attempts_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
            return True, None
            
        try:
            cache.set(attempts_key, attempts + 1, timeout=300)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
        return False, f"Invalid OTP. {3 - (attempts + 1)} attempts left."

    @staticmethod
    def delete_otp(email, purpose='auth'):
        email = email.lower() 
        key = f"otp:{purpose}:{email}"
        try:
            cache.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    @staticmethod
    def mask_email(email):
        email = email.lower() 
        try:
            user_part, domain_part = email.split('@')
            if len(user_part) <= 2:
                masked_user = user_part + "*"
            else:
                masked_user = user_part[:2] + "*" * (len(user_part) - 2)
            return f"{masked_user}@{domain_part}"
        except Exception:
            return email

    @staticmethod
    def send_otp_email(email, otp, purpose_text="verification"):
        subject = f"[{purpose_text.upper()}] Your ParseOps OTP Code: {otp}"
        
        message = (
            f"Hello,\n\n"
            f"Your {purpose_text} OTP code for ParseOps is: {otp}\n\n"
            f"This code will expire in 5 minutes for security reasons.\n"
            f"If you did not request this code, please ignore this email or contact support.\n\n"
            f"Best regards,\n"
            f"The ParseOps Security Team"
        )
        
        print("\n" + "="*80)
        print(f"[PARSEOPS DEV SECURITY] NEW OTP GENERATED")
        print(f"EMAIL:   {email}")
        print(f"PURPOSE: {purpose_text.upper()}")
        print(f"OTP CODE: {otp}")
        print("="*80 + "\n")
        
        import threading
        def _send_async():
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                print(f"DEBUG: Successfully sent OTP email to {email}")
            except Exception as e:
                print(f"ERROR: Failed to send OTP email to {email}: {str(e)}")
                logger.error(f"Failed to send OTP email to {email}: {str(e)}")

        threading.Thread(target=_send_async, daemon=True).start()
        return True

    @staticmethod
    def store_temp_data(email, data, timeout=600):
        email = email.lower() # Normalize
        key = f"temp_reg:{email}"
        try:
            cache.set(key, data, timeout=timeout)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
        return key

    @staticmethod
    def get_temp_data(email):
        email = email.lower() 
        key = f"temp_reg:{email}"
        return cache.get(key)

    @staticmethod
    def can_resend(email, purpose='auth'):
        email = email.lower() 
        key = f"resend_cooldown:{purpose}:{email}"
        
        if cache.get(key) is not None:
            return False, 60
        
        cache.set(key, "blocked", timeout=60)
        return True, None
