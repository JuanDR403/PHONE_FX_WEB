from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required  # Opcional
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import json
from usuarios.models import Usuarios
from dispositivos.models import Dispositivo

from citas.models import Cita, HistorialCita

def tiene_permiso(request, roles_permitidos):
    if not request.user.is_authenticated:
        return False
    perfil = getattr(request.user, 'perfil_usuarios', None)
    if perfil and perfil.id_rol and perfil.id_rol.nombre:
        # Convertir a minúsculas para comparación case-insensitive
        rol_actual = perfil.id_rol.nombre.lower()
        roles_permitidos_lower = [r.lower() for r in roles_permitidos]
        return rol_actual in roles_permitidos_lower
    return False


@csrf_exempt
def actualizar_observacion(request, id):
    if not tiene_permiso(request, ['Admin', 'cliente']):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        nueva_obs = data.get('observaciones', '').strip()
        try:
            historial = HistorialCita.objects.get(idhistorial=id)
            historial.observaciones = nueva_obs
            historial.save()
            return JsonResponse({'success': True})
        except HistorialCita.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No encontrado'})
    return JsonResponse({'success': False, 'error': 'Método inválido'})

@login_required  # Elimina este decorador si quieres acceso público
@login_required
def home(request):
    if hasattr(request.user, 'perfil_usuarios') and request.user.perfil_usuarios.id_rol:
        rol = request.user.perfil_usuarios.id_rol.nombre.lower()
    else:
        rol = ''

    qs = (
        Cita.objects.select_related('cliente', 'asesor', 'dispositivo')
        .prefetch_related('historiales')
    )

    if rol == 'cliente' and hasattr(request.user, 'perfil_usuarios'):
        qs = qs.filter(cliente=request.user.perfil_usuarios)
    else:
        qs = qs.all()

    citas = qs.order_by('-idcita')

    # 🔹 Convertimos fecha/hora a string para evitar error de utcoffset
    for c in citas:
        try:
            c.fecha_cita_str = c.fecha_cita.strftime('%Y-%m-%d')
        except AttributeError:
            c.fecha_cita_str = str(c.fecha_cita)  # si ya es string
        try:
            c.hora_cita_str = c.hora_cita.strftime('%H:%M')
        except AttributeError:
            c.hora_cita_str = str(c.hora_cita)

    asesores = Usuarios.objects.filter(id_rol__idrol=2)
    dispositivos_cliente = Dispositivo.objects.filter(cliente=request.user.perfil_usuarios) if rol == 'cliente' else None

    context = {
        'titulo': 'Página de Inicio',
        'mensaje': 'Hola, Bienvenido a PhoneFX',
        'citas': citas,
        'rol': rol,
        'asesores': asesores,
        'dispositivos_cliente': dispositivos_cliente,
    }
    return render(request, 'inicio/home.html', context)





@login_required
@require_POST
@transaction.atomic
def actualizar_estado_cita(request):
    if not tiene_permiso(request, ['Admin', 'asesor']):
        return JsonResponse({'ok': False, 'error': 'Sin permiso'}, status=403)
    try:
        cita_id = int(request.POST.get('cita_id'))
        nuevo_estado = request.POST.get('estado')
        observacion = (request.POST.get('observacion') or '').strip()
        if not nuevo_estado:
            return JsonResponse({'ok': False, 'error': 'Estado no proporcionado.'}, status=400)
        # Validar contra los estados permitidos para evitar errores de base de datos
        estados_validos = {'pendiente', 'en proceso', 'finalizado', 'olvidado'}
        if nuevo_estado not in estados_validos:
            return JsonResponse({'ok': False, 'error': 'Estado inválido.'}, status=400)

        cita = Cita.objects.select_for_update().get(idcita=cita_id)
        estado_anterior = cita.estado or ''
        if estado_anterior == nuevo_estado:
            return JsonResponse({'ok': True, 'unchanged': True})

        # Actualiza el estado de la cita
        cita.estado = nuevo_estado
        cita.save(update_fields=['estado'])

        # Mapa para mostrar etiquetas legibles
        etiqueta = {
            'pendiente': 'Solicitud',
            'en proceso': 'En Proceso',
            'finalizado': 'Finalizado',
            'olvidado': 'Olvidado',
        }

        nuevo_hist = None
        # Intenta registrar en historial si la tabla es editable
        try:
            nuevo_hist = HistorialCita.objects.create(
                cita=cita,
                estado_anterior=etiqueta.get(estado_anterior, estado_anterior or 'Solicitud'),
                estado_nuevo=etiqueta.get(nuevo_estado, nuevo_estado),
                observaciones=observacion or '—'
            )
        except Exception:
            # Si no se puede escribir (managed=False o sin permisos), lo ignoramos
            pass

        # Devuelve información para actualizar el badge en la UI
        badge = {
            'finalizado': {'cls': 'success', 'label': 'Finalizado'},
            'en proceso': {'cls': 'info', 'label': 'En Proceso'},
            'pendiente': {'cls': 'warning', 'label': 'Solicitud'},
            'olvidado': {'cls': 'danger', 'label': 'Olvidado'},
        }.get(nuevo_estado, {'cls': 'secondary', 'label': etiqueta.get(nuevo_estado, nuevo_estado)})

        # Empaquetar el historial recién creado (si existe)
        hist_json = None
        if nuevo_hist is not None:
            hist_json = {
                'id': nuevo_hist.idhistorial,
                'fecha': nuevo_hist.fecha_cambio.strftime('%Y-%m-%d %H:%M'),
                'estado_anterior': nuevo_hist.estado_anterior,
                'estado_nuevo': nuevo_hist.estado_nuevo,
                'observaciones': nuevo_hist.observaciones or '—',
            }

        return JsonResponse({'ok': True, 'estado': nuevo_estado, 'badge': badge, 'historial': hist_json})
    except Cita.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Cita no encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def actualizar_descripcion_cita(request):
    if not tiene_permiso(request, ['admin', 'cliente']):
        return JsonResponse({'success': False, 'error': 'No tienes permisos para esta acción'}, status=403)

    try:
        cita_id = request.POST.get('cita_id')
        nueva_descripcion = request.POST.get('descripcion', '').strip()

        if not cita_id:
            return JsonResponse({'success': False, 'error': 'ID de cita no proporcionado'}, status=400)

        cita = Cita.objects.get(idcita=cita_id)

        # 🔹 VALIDACIÓN EXTRA: Si es cliente, solo puede editar sus propias citas
        if request.user.perfil_usuarios.id_rol.nombre.lower() == 'cliente':
            if cita.cliente != request.user.perfil_usuarios:
                return JsonResponse({'success': False, 'error': 'Solo puedes editar tus propias citas'}, status=403)

        # Actualizar la descripción/observaciones
        cita.observaciones = nueva_descripcion
        cita.save(update_fields=['observaciones'])

        return JsonResponse({'success': True})

    except Cita.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cita no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)