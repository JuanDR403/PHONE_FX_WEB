from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from productos.models import Producto, Categoria
from .forms import ProductoForm

# Vista de la tienda: lista de productos con filtro por categoría
def tiene_permiso(request, roles_permitidos):
    if not request.user.is_authenticated:
        return False
    perfil = getattr(request.user, 'perfil_usuarios', None)
    if perfil and perfil.id_rol and perfil.id_rol.nombre.lower() in [r.lower() for r in roles_permitidos]:
        return True
    return False

def lista_productos(request):
    rol = request.user.perfil_usuarios.id_rol.nombre if hasattr(request.user, 'perfil_usuarios') else ''

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
        'rol': rol,
    }
    return render(request, 'tienda/lista_productos.html', context)


def crear_producto(request):
    if not tiene_permiso(request, ['Admin', 'asesor']):
        return redirect('tienda:lista_productos')

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            imagen_subida = request.FILES.get('imagen_archivo')
            if imagen_subida:
                fs = FileSystemStorage()
                filename = fs.save(f"productos/{imagen_subida.name}", imagen_subida)
                producto.imagen = settings.MEDIA_URL + filename  # guardamos URL servible
            producto.save()
            return redirect(reverse('tienda:lista_productos'))
    else:
        form = ProductoForm()
    return render(request, 'tienda/crear_producto.html', {'form': form})


def editar_producto(request, idproducto):
    if not tiene_permiso(request, ['Admin', 'asesor']):
        return redirect('tienda:lista_productos')

    producto = get_object_or_404(Producto, pk=idproducto)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save(commit=False)
            imagen_subida = request.FILES.get('imagen_archivo')
            if imagen_subida:
                fs = FileSystemStorage()
                filename = fs.save(f"productos/{imagen_subida.name}", imagen_subida)
                producto.imagen = settings.MEDIA_URL + filename
            producto.save()
            return redirect(reverse('tienda:lista_productos'))
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'tienda/editar_producto.html', {'form': form, 'producto': producto})


@require_POST
def eliminar_producto(request, idproducto):
    if not tiene_permiso(request, ['Admin', 'asesor']):
        return redirect('tienda:lista_productos')

    producto = get_object_or_404(Producto, pk=idproducto)
    producto.delete()
    return redirect(reverse('tienda:lista_productos'))
