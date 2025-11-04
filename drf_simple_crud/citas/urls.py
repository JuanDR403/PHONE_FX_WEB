from django.urls import path
from .views import agendar_cita
from . import  views


app_name = 'citas'

urlpatterns = [
    path('crear/', agendar_cita, name='agendar_cita'),
    path('agregar-dispositivo/', views.agregar_dispositivo_ajax, name='agregar_dispositivo'),
    path('verificar-fecha/', views.verificar_disponibilidad_fecha, name='verificar_fecha'),
]
