from django.urls import path
from . import views

app_name = 'logueo'

urlpatterns = [
    path('', views.login_view, name='login'),  # Ahora responde a /login/
    path('logout/', views.logout_view, name='logout'),  # URL para cerrar sesión
]
