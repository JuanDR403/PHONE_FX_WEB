# tienda/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib import messages
from productos.models import Producto, Categoria
from .forms import ProductoForm


def tiene_permiso(request, roles_permitidos):
    if not request.user.is_authenticated:
        return False
    perfil = getattr(request.user, 'perfil_usuarios', None)
    if perfil and perfil.id_rol and perfil.id_rol.nombre:
        rol_actual = perfil.id_rol.nombre.lower()
        roles_permitidos_lower = [r.lower() for r in roles_permitidos]
        return rol_actual in roles_permitidos_lower
    return False


def lista_productos(request):
    # Obtener rol en minúsculas para consistencia
    if hasattr(request.user, 'perfil_usuarios') and request.user.perfil_usuarios.id_rol:
        rol = request.user.perfil_usuarios.id_rol.nombre.lower()
    else:
        rol = ''

    categoria_id = request.GET.get('categoria')
    categorias = Categoria.objects.all()
    productos = Producto.objects.select_related('categoria').all()

    if categoria_id:
        try:
            productos = productos.filter(categoria_id=int(categoria_id))
        except (ValueError, TypeError):
            pass

    context = {
        'categorias': categorias,
        'productos': productos,
        'categoria_seleccionada': int(categoria_id) if categoria_id and categoria_id.isdigit() else None,
        'rol': rol,
    }
    return render(request, 'tienda/lista_productos.html', context)


def crear_producto(request):
    if not tiene_permiso(request, ['admin', 'asesor']):
        messages.error(request, '❌ No tienes permisos para crear productos.')
        return redirect('tienda:lista_productos')

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            imagen_subida = request.FILES.get('imagen_archivo')
            if imagen_subida:
                fs = FileSystemStorage()
                filename = fs.save(f"productos/{imagen_subida.name}", imagen_subida)
                producto.imagen = settings.MEDIA_URL + filename
            producto.save()
            messages.success(request, '✅ Producto creado exitosamente.')
            return redirect(reverse('tienda:lista_productos'))
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario.')
    else:
        form = ProductoForm()

    return render(request, 'tienda/crear_producto.html', {'form': form})


def editar_producto(request, idproducto):
    if not tiene_permiso(request, ['admin', 'asesor']):
        messages.error(request, '❌ No tienes permisos para editar productos.')
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
            messages.success(request, '✅ Producto actualizado exitosamente.')
            return redirect(reverse('tienda:lista_productos'))
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'tienda/editar_producto.html', {'form': form, 'producto': producto})


@require_POST
def eliminar_producto(request, idproducto):
    if not tiene_permiso(request, ['admin', 'asesor']):
        messages.error(request, '❌ No tienes permisos para eliminar productos.')
        return redirect('tienda:lista_productos')

    producto = get_object_or_404(Producto, pk=idproducto)
    nombre_producto = producto.nombre
    producto.delete()
    messages.success(request, f'✅ Producto "{nombre_producto}" eliminado exitosamente.')
    return redirect(reverse('tienda:lista_productos'))