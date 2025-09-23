from django.shortcuts import render
from productos.models import Producto, Categoria

# Vista de la tienda: lista de productos con filtro por categoría

def lista_productos(request):
    categoria_id = request.GET.get('categoria')

    categorias = Categoria.objects.all()
    productos = Producto.objects.select_related('categoria').all()

    if categoria_id:
        try:
            productos = productos.filter(categoria_id=int(categoria_id))
        except (ValueError, TypeError):
            # Si el parámetro no es válido, no filtra
            pass

    context = {
        'categorias': categorias,
        'productos': productos,
        'categoria_seleccionada': int(categoria_id) if categoria_id and categoria_id.isdigit() else None,
    }
    return render(request, 'tienda/lista_productos.html', context)
