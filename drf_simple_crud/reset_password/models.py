from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from datetime import timedelta

User = get_user_model()


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=1)

    class Meta:
        verbose_name = "Código de recuperación"
        verbose_name_plural = "Códigos de recuperación"