from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class ActivationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activation_token')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(seconds=30)