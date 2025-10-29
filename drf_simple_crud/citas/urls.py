from django.urls import path
from .views import agendar_cita

app_name = 'citas'

urlpatterns = [
    path('crear/', agendar_cita, name='agendar_cita'),

]
