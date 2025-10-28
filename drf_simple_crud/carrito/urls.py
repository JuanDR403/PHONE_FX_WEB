from django.urls import path
from . import views

app_name = 'carrito'

urlpatterns = [
    path('ver/', views.ver_carrito, name='ver_carrito'),
    path('agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('incrementar/', views.incrementar_cantidad, name='incrementar_cantidad'),
    path('decrementar/', views.decrementar_cantidad, name='decrementar_cantidad'),

    # Mercado Pago endpoints
    path('pagos/mercadopago/preference/', views.mp_create_preference, name='mp_create_preference'),
    path('pagos/mercadopago/webhook/', views.mp_webhook, name='mp_webhook'),
    path('pagos/mercadopago/retorno/', views.mp_return, name='mp_return'),
]
