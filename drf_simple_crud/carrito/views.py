from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import mercadopago

from .models import Carrito, CarritoDetalle
from usuarios.models import Usuarios
from productos.models import Producto


# Mercado Pago: SDK client helper

def mp_client():
    return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)


@require_POST
@login_required
def mp_create_preference(request):
    # Map auth user to profile
    try:
        perfil = Usuarios.objects.get(user=request.user)
    except Usuarios.DoesNotExist:
        return JsonResponse({"error": "Perfil de usuario no encontrado"}, status=400)

    carrito, _ = Carrito.objects.get_or_create(cliente=perfil)

    # Build items from cart details
    detalles = (
        CarritoDetalle.objects
        .select_related('producto')
        .filter(carrito=carrito)
    )

    items = []
    currency = 'COP'
    subtotal = Decimal('0')
    for d in detalles:
        if not d.producto:
            continue
        title = d.producto.nombre or f"Producto {d.producto_id}"
        unit_price = _to_decimal(d.producto.precio)
        quantity = int(d.cantidad or 0)
        if quantity <= 0:
            continue
        subtotal += unit_price * quantity
        items.append({
            "id": str(d.producto_id),
            "title": title,
            "quantity": quantity,
            "currency_id": currency,
            "unit_price": float(unit_price),
        })

    if not items:
        return JsonResponse({"error": "El carrito está vacío"}, status=400)

    # back URLs and webhook
    success_url = request.build_absolute_uri(reverse('carrito:mp_return') + '?status=success')
    failure_url = request.build_absolute_uri(reverse('carrito:mp_return') + '?status=failure')
    pending_url = request.build_absolute_uri(reverse('carrito:mp_return') + '?status=pending')

    notification_url = settings.MERCADOPAGO_WEBHOOK_URL or request.build_absolute_uri(reverse('carrito:mp_webhook'))

    preference_data = {
        "items": items,
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        },
        # "notification_url": notification_url,  # deshabilitado en desarrollo local
        "external_reference": f"CART-{carrito.idcarrito}",
        # Uncomment to tweak methods; by default all available methods are shown
        # "payment_methods": {
        #     "installments": 12,
        # }
    }

    sdk = mp_client()
    try:
        result = sdk.preference().create(preference_data)
    except Exception as e:
        return JsonResponse({"error": "Error al crear preferencia", "detail": str(e)}, status=500)

    if result.get("status") not in (200, 201):
        return JsonResponse({"error": "No se pudo crear la preferencia", "detail": result}, status=400)

    pref = result["response"]
    return JsonResponse({
        "preference_id": pref.get("id"),
        "init_point": pref.get("init_point"),
        "sandbox_init_point": pref.get("sandbox_init_point"),
        "public_key": settings.MERCADOPAGO_PUBLIC_KEY,
    })


@csrf_exempt
def mp_webhook(request):
    # Acknowledge quickly
    type_ = request.GET.get("type") or request.POST.get("type")
    payment_id = request.GET.get("data.id") or request.POST.get("data.id")
    # Minimal validation
    if type_ == 'payment' and payment_id:
        # Optionally, retrieve payment to verify
        try:
            payment = mp_client().payment().get(payment_id)
            # You could update your order status based on payment['response']['status']
        except Exception:
            pass
    return HttpResponse("OK", status=200)


def mp_return(request):
    status = request.GET.get('status')
    if status == 'success':
        messages.success(request, 'Pago aprobado en Mercado Pago. ¡Gracias!')
    elif status == 'pending':
        messages.info(request, 'Pago pendiente. Te notificaremos cuando se acredite.')
    else:
        messages.error(request, 'El pago no pudo completarse o fue cancelado.')
    return redirect('carrito:ver_carrito')


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
        'mp_public_key': settings.MERCADOPAGO_PUBLIC_KEY,
    }
    return render(request, 'carrito/ver_carrito.html', context)
#anadir al front end de la vista publica

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
