from django.urls import path
from . import views

app_name = 'registro'

urlpatterns = [
    path('', views.registro, name='registro'),
    path('ajax/', views.registro_ajax, name='registro_ajax'),
    path('verificar/', views.verificar_registro, name='verificar_registro'),
    path('reenviar-codigo/', views.reenviar_codigo, name='reenviar_codigo'),
]