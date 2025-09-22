from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from .utils import send_email

def send_activation_email_task(user_id, user_email):
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    
    activation_link = f"http://127.0.0.1:5500/pages/auth/activate.html?uid={uidb64}&token={token}"
    
    send_email(subject="Confirm your email",
                recipient=user_email,
                template_name="emails/activation_email.html",
                link=activation_link,
                text_content="Click the link to activate your account:")

def send_password_reset_email(user_email, token, uidb64):
   reset_url = f"http://127.0.0.1:5500/pages/auth/confirm_password.html?uid={uidb64}&token={token}"

   send_email(subject="Reset your Password",
                recipient=user_email,
                template_name="emails/password_reset_email.html",
                link=reset_url,
                text_content="Click the link to reset your password:")