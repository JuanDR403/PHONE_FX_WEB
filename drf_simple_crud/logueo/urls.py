from django.urls import path
from . import views

app_name = 'logueo'

urlpatterns = [
    path('', views.login_view, name='login'),  # Ahora responde a /login/
]