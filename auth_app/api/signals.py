from django.dispatch import Signal

# Signal triggered after a new user successfully registers.
user_registered = Signal()

# Signal triggered when a user requests a password reset.
password_reset_requested = Signal()