from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CitaForm
from .models import Cita
from dispositivos.forms import DispositivoForm  # debes crear este si aún no lo tienes
from dispositivos.models import Dispositivo
from datetime import datetime

@login_required
def agendar_cita(request):
    dispositivo_form = None

    if request.method == 'POST':
        cliente = request.user.perfil_usuarios  # ✅ Tomamos el cliente desde el usuario logueado
        asesor_id = request.POST.get('asesor')
        fecha_str = request.POST.get('fecha_cita')
        hora_str = request.POST.get('hora_cita')
        tipo_servicio = request.POST.get('tipo_servicio')
        observaciones = request.POST.get('observaciones')

        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora = datetime.strptime(hora_str, '%H:%M').time()

        # Verificar si seleccionó "otro dispositivo"
        if request.POST.get('dispositivo') == 'otro':
            dispositivo_form = DispositivoForm(request.POST)
            if dispositivo_form.is_valid():
                nuevo_dispositivo = dispositivo_form.save(commit=False)
                nuevo_dispositivo.cliente = cliente
                nuevo_dispositivo.save()
                dispositivo = nuevo_dispositivo
            else:
                # Si el formulario no es válido, renderizamos con errores
                return render(request, 'citas/agendar_cita.html', {
                    'form': CitaForm(),
                    'dispositivo_form': dispositivo_form
                })
        else:
            dispositivo_id = request.POST.get('dispositivo')
            dispositivo = Dispositivo.objects.get(pk=dispositivo_id)

        # Guardar la cita
        Cita.objects.create(
            cliente=cliente,
            asesor_id=asesor_id,
            dispositivo=dispositivo,
            fecha_cita=fecha,
            hora_cita=hora,
            tipo_servicio=tipo_servicio,
            observaciones=observaciones
        )

        return redirect('inicio:home')

    # GET: formulario normal
    form = CitaForm(request=request)
    return render(request, 'citas/agendar_cita.html', {
        'form': form,
        'dispositivo_form': dispositivo_form
    })