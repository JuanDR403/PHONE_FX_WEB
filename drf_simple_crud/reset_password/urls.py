from django.urls import path
from .views import PasswordResetRequestPageView # Asegúrate de importar la nueva vista

urlpatterns = [
    # ... otras urls ...
    path('password-reset-request/', PasswordResetRequestPageView.as_view(), name='password_reset_request_page'),
    # ...
]