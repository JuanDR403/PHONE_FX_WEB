from django.urls import path
from .views import PasswordResetRequestView, PasswordResetVerifyView

app_name = 'reset_password'

urlpatterns = [
    path('request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('verify/', PasswordResetVerifyView.as_view(), name='password_reset_verify'),
]