from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetCode

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetVerifySerializer(serializers.Serializer):
    code = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8)