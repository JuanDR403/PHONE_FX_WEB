# citas/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from .forms import CitaForm
from django.contrib import messages
from .models import Cita
from dispositivos.forms import DispositivoForm
from dispositivos.models import Dispositivo
from datetime import datetime
from .utils import tiene_permiso, obtener_rol_usuario


@login_required
def agregar_dispositivo_ajax(request):
    """Vista específica para agregar dispositivos via AJAX"""
    # 👈 Verificación de permisos
    if not tiene_permiso(request, ['admin', 'cliente']):
        return HttpResponseForbidden("No tienes permisos para realizar esta acción")
    print("DEBUG: agregar_dispositivo_ajax llamada")

    if request.method == 'POST':
        print(f"DEBUG: Datos POST: {request.POST}")

        # Crear el formulario con los datos
        dispositivo_form = DispositivoForm(request.POST)
        print(f"DEBUG: Formulario creado")

        if dispositivo_form.is_valid():
            print("DEBUG: Formulario válido")
            nuevo_dispositivo = dispositivo_form.save(commit=False)
            nuevo_dispositivo.cliente = request.user.perfil_usuarios
            nuevo_dispositivo.save()
            print(f"DEBUG: Dispositivo guardado - ID: {nuevo_dispositivo.iddispositivo}")

            return JsonResponse({
                'success': True,
                'dispositivo_id': nuevo_dispositivo.iddispositivo,
                'dispositivo_text': f"{nuevo_dispositivo.marca} {nuevo_dispositivo.modelo}"
            })
        else:
            print(f"DEBUG: Errores del formulario: {dispositivo_form.errors}")
            return JsonResponse({
                'success': False,
                'errors': dispositivo_form.errors
            })

    return JsonResponse({
        'success': False,
        'errors': {'__all__': ['Método no permitido']}
    }, status=405)


@login_required
def agendar_cita(request):
    """Vista principal para agendar citas"""
    if not tiene_permiso(request, ['admin', 'cliente']):
        messages.error(request,
                       '❌ No tienes permisos para acceder a esta página. Solo usuarios con rol de Admin o Cliente pueden agendar citas.')
        return redirect('inicio:home')
    rol_usuario = obtener_rol_usuario(request)
    if request.method == 'POST':
        # ✅ CORREGIDO: Pasar request al formulario también en POST
        form = CitaForm(request.POST, request=request)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cliente = request.user.perfil_usuarios
            cita.save()
            return redirect('inicio:home')
        else:
            print("❌ ERRORES DEL FORMULARIO:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
            print("📦 DATOS POST:", dict(request.POST))

            dispositivo_form = DispositivoForm()
            return render(request, 'citas/agendar_cita.html', {
                'form': form,
                'dispositivo_form': dispositivo_form,
                'rol': rol_usuario
            })
    else:
        # GET request
        form = CitaForm(request=request)

    return render(request, 'citas/agendar_cita.html', {
        'form': form,
        'dispositivo_form': DispositivoForm(),
        'rol': rol_usuario
    })

def verificar_disponibilidad_fecha(request):
    """Vista para verificar disponibilidad de fecha via AJAX"""
    if not tiene_permiso(request, ['admin', 'cliente']):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            existe_cita = Cita.objects.filter(fecha_cita=fecha).exists()
            return JsonResponse({'disponible': not existe_cita})
        except ValueError:
            return JsonResponse({'disponible': False})
    return JsonResponse({'disponible': False})