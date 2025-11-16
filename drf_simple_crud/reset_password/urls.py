from django.urls import path
from .views import PasswordResetRequestPageView, PasswordResetVerifyPageView

app_name = 'reset_password'

urlpatterns = [

    path('password-reset-request/', PasswordResetRequestPageView.as_view(), name='request_reset'),
path('verify-code/', PasswordResetVerifyPageView.as_view(), name='verify_code'),
    # ...
]