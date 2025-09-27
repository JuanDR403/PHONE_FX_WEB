from django.urls import path
from . import views

app_name = 'carrito'

urlpatterns = [
    path('ver/', views.ver_carrito, name='ver_carrito'),
    path('agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('incrementar/', views.incrementar_cantidad, name='incrementar_cantidad'),
    path('decrementar/', views.decrementar_cantidad, name='decrementar_cantidad'),
]
