from django.shortcuts import render
from .models import Categoria, Producto

def vista_tabla_productos(request):
    categorias = Categoria.objects.all()
    productos = Producto.objects.select_related('categoria').all()
    return render(request, 'productos/tabla_productos.html', {
        'categorias': categorias,
        'productos': productos
    })