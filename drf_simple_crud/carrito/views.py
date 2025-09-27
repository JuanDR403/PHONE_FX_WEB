from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages

from .models import Carrito, CarritoDetalle
from usuarios.models import Usuarios
from productos.models import Producto


def _to_decimal(value):
    if value is None:
        return Decimal('0')
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    # Normalize common currency-formatted strings like "$ 1.234,56" or "1,234.56"
    s = str(value).strip()

    # Remove currency symbols and letters
    symbols = ['$', '€', '£', '₡', '₳', '₺', 'R$', 'S/']
    for sym in symbols:
        s = s.replace(sym, '')
    # Remove spaces and non-breaking spaces
    s = s.replace('\xa0', '').replace(' ', '')

    # Decide decimal separator and remove thousand separators
    has_comma = ',' in s
    has_dot = '.' in s
    if has_comma and has_dot:
        # Use the rightmost separator as decimal; remove the other
        if s.rfind(',') > s.rfind('.'):
            # Decimal comma: remove dots, replace last comma with dot
            s = s.replace('.', '')
            s = s.replace(',', '.')
        else:
            # Decimal dot: remove commas
            s = s.replace(',', '')
    elif has_comma and not has_dot:
        # Only comma present: treat as decimal separator
        s = s.replace(',', '.')
    elif has_dot and not has_comma:
        # Only dot present: in Colombian-style inputs like "15.000" or "1.234.567"
        # the dot is thousands separator. Detect pattern ddd.ddd and strip dots.
        import re
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
            s = s.replace('.', '')
        # else: leave as-is to allow true decimal dot like "123.45"
    # else: only none -> already fine

    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal('0')


def _format_cop_no_cents(value: Decimal) -> str:
    """Format a number as Colombian-style currency without cents: 1.234.567
    - Rounds half up to the nearest peso.
    - Uses dot as thousands separator.
    """
    if value is None:
        value = Decimal('0')
    try:
        q = Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    except Exception:
        q = Decimal('0')
    return f"{q:,.0f}".replace(',', '.')


@login_required
def ver_carrito(request):
    # Map auth user to our Usuarios profile (if exists)
    try:
        perfil = Usuarios.objects.get(user=request.user)
    except Usuarios.DoesNotExist:
        perfil = None

    items = []
    subtotal = Decimal('0')

    if perfil is not None:
        # Ensure the user has a cart
        carrito, _created = Carrito.objects.get_or_create(cliente=perfil)

        # Fetch details with related product
        detalles = (
            CarritoDetalle.objects
            .select_related('producto')
            .filter(carrito=carrito)
        )

        for d in detalles:
            nombre = d.producto.nombre if d.producto else 'Producto no disponible'
            precio_unit = _to_decimal(d.producto.precio) if d.producto else Decimal('0')
            cantidad = d.cantidad or 0
            total_linea = precio_unit * Decimal(cantidad)
            subtotal += total_linea
            items.append({
                'nombre': nombre,
                'precio_unit': precio_unit,
                'precio_unit_str': _format_cop_no_cents(precio_unit),
                'cantidad': cantidad,
                'total_linea': total_linea,
                'total_linea_str': _format_cop_no_cents(total_linea),
                'producto': d.producto,
                'idcarritodetalle': d.idcarritodetalle,
            })

    context = {
        'items': items,
        'subtotal': subtotal,
        'subtotal_str': _format_cop_no_cents(subtotal),
        'tiene_perfil': perfil is not None,
    }
    return render(request, 'carrito/ver_carrito.html', context)


@login_required
@transaction.atomic
def agregar_al_carrito(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Método no permitido')

    producto_id = request.POST.get('producto_id')
    redirect_to_cart = request.POST.get('comprar_ahora') == '1'

    # Map auth user to Usuarios profile
    try:
        perfil = Usuarios.objects.select_for_update().get(user=request.user)
    except Usuarios.DoesNotExist:
        return HttpResponseBadRequest('Perfil de usuario no encontrado')

    producto = get_object_or_404(Producto.objects.select_for_update(), pk=producto_id)

    if not producto.stock or producto.stock <= 0:
        # Sin stock
        if redirect_to_cart:
            return redirect(reverse('carrito:ver_carrito'))
        # Volver a donde estaba
        return redirect(request.META.get('HTTP_REFERER') or reverse('tienda:lista_productos'))

    carrito, _ = Carrito.objects.get_or_create(cliente=perfil)

    # Buscar si ya existe el detalle del mismo producto
    detalle, created = CarritoDetalle.objects.select_for_update().get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': 0}
    )
    detalle.cantidad = (detalle.cantidad or 0) + 1
    detalle.save()

    # Decrementar stock
    producto.stock = (producto.stock or 0) - 1
    producto.save(update_fields=['stock'])

    if redirect_to_cart:
        return redirect(reverse('carrito:ver_carrito'))
    return redirect(request.META.get('HTTP_REFERER') or reverse('tienda:lista_productos'))


@login_required
@transaction.atomic
def eliminar_del_carrito(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Método no permitido')

    detalle_id = request.POST.get('detalle_id')
    # Map user to profile and ensure the detail belongs to their cart
    try:
        perfil = Usuarios.objects.select_for_update().get(user=request.user)
    except Usuarios.DoesNotExist:
        return HttpResponseBadRequest('Perfil de usuario no encontrado')

    carrito = get_object_or_404(Carrito, cliente=perfil)
    detalle = get_object_or_404(CarritoDetalle.objects.select_for_update(), pk=detalle_id, carrito=carrito)

    cantidad = detalle.cantidad or 0
    producto = None
    if detalle.producto_id:
        producto = Producto.objects.select_for_update().filter(pk=detalle.producto_id).first()

    # Eliminar el detalle del carrito
    detalle.delete()

    # Restaurar stock si el producto aún existe
    if producto is not None and cantidad > 0:
        producto.stock = (producto.stock or 0) + cantidad
        producto.save(update_fields=['stock'])

    return redirect(request.META.get('HTTP_REFERER') or reverse('carrito:ver_carrito'))


@login_required
@transaction.atomic
def incrementar_cantidad(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Método no permitido')

    detalle_id = request.POST.get('detalle_id')

    try:
        perfil = Usuarios.objects.select_for_update().get(user=request.user)
    except Usuarios.DoesNotExist:
        return HttpResponseBadRequest('Perfil de usuario no encontrado')

    carrito = get_object_or_404(Carrito, cliente=perfil)
    detalle = get_object_or_404(CarritoDetalle.objects.select_for_update(), pk=detalle_id, carrito=carrito)

    if not detalle.producto_id:
        messages.error(request, 'Este producto ya no está disponible.')
        # Eliminar la línea huérfana
        detalle.delete()
        return redirect(request.META.get('HTTP_REFERER') or reverse('carrito:ver_carrito'))

    producto = get_object_or_404(Producto.objects.select_for_update(), pk=detalle.producto_id)

    if not producto.stock or producto.stock <= 0:
        messages.error(request, 'No hay más stock disponible de este producto.')
        return redirect(request.META.get('HTTP_REFERER') or reverse('carrito:ver_carrito'))

    # Incrementar cantidad en carrito y decrementar stock
    detalle.cantidad = (detalle.cantidad or 0) + 1
    detalle.save(update_fields=['cantidad'])

    producto.stock = (producto.stock or 0) - 1
    producto.save(update_fields=['stock'])

    return redirect(request.META.get('HTTP_REFERER') or reverse('carrito:ver_carrito'))


@login_required
@transaction.atomic
def decrementar_cantidad(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Método no permitido')

    detalle_id = request.POST.get('detalle_id')

    try:
        perfil = Usuarios.objects.select_for_update().get(user=request.user)
    except Usuarios.DoesNotExist:
        return HttpResponseBadRequest('Perfil de usuario no encontrado')

    carrito = get_object_or_404(Carrito, cliente=perfil)
    detalle = get_object_or_404(CarritoDetalle.objects.select_for_update(), pk=detalle_id, carrito=carrito)

    if not detalle.producto_id:
        # El producto ya no existe; solo elimina la línea si corresponde
        detalle.delete()
        return redirect(request.META.get('HTTP_REFERER') or reverse('carrito:ver_carrito'))

    producto = get_object_or_404(Producto.objects.select_for_update(), pk=detalle.producto_id)

    cantidad_actual = detalle.cantidad or 0
    if cantidad_actual <= 1:
        # Comportamiento: si queda en 1 y se resta, eliminar del carrito y devolver 1 al stock
        detalle.delete()
        producto.stock = (producto.stock or 0) + 1
        producto.save(update_fields=['stock'])
        return redirect(request.META.get('HTTP_REFERER') or reverse('carrito:ver_carrito'))

    # Disminuir cantidad y devolver stock en 1
    detalle.cantidad = cantidad_actual - 1
    detalle.save(update_fields=['cantidad'])

    producto.stock = (producto.stock or 0) + 1
    producto.save(update_fields=['stock'])

    return redirect(request.META.get('HTTP_REFERER') or reverse('carrito:ver_carrito'))
