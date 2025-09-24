from django.urls import path
from . import views

app_name = 'tienda'

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('producto/nuevo/', views.crear_producto, name='crear_producto'),
    path('producto/<int:idproducto>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:idproducto>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
]
