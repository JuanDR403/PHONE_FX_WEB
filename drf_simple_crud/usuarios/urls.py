from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('profile/', views.edit_profile, name='edit_profile'),
]