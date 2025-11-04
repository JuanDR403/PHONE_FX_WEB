from django.urls import path
from . import views

app_name = 'inicio'

urlpatterns = [
    path('', views.home, name='home'),  # Responde a /home/
    path('actualizar-estado/', views.actualizar_estado_cita, name='actualizar_estado_cita'),
    path('actualizar-observacion/<int:id>/', views.actualizar_observacion, name='actualizar_observacion'),
    path('actualizar-descripcion-cita/', views.actualizar_descripcion_cita, name='actualizar_descripcion_cita'),
]