from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from usuarios.models import Usuarios
from .forms import UserProfileForm
from django.conf import settings
from PIL import Image

@login_required
def edit_profile(request):
    try:
        usuario = Usuarios.objects.get(user=request.user)
    except Usuarios.DoesNotExist:
        messages.error(request, "No se encontró el usuario.")
        return redirect('inicio:home')

    if request.method == 'POST':
        # Si solo se envió la foto desde el botón de "Subir foto"
        if request.POST.get('photo_form_submitted') == '1' and 'foto_perfil' in request.FILES:
            usuario.foto_perfil = request.FILES['foto_perfil']
            usuario.save()
            messages.success(request, 'Tu foto de perfil ha sido actualizada correctamente.')
            return redirect('usuarios:edit_profile')

        form = UserProfileForm(request.POST, request.FILES, instance=usuario)

        # Validación de correo duplicado
        correo = request.POST.get('correo')
        if correo and Usuarios.objects.filter(correo=correo).exclude(pk=usuario.pk).exists():
            messages.error(request, 'Este correo electrónico ya está registrado.')
            return render(request, 'usuarios/edit_profile.html', {
                'form': form,
                'usuario': usuario,
                'title': 'Editar Perfil'
            })

        if form.is_valid():
            usuario = form.save(commit=False)

            # Si hay nueva contraseña
            nueva = form.cleaned_data.get('new_password')
            if nueva:
                usuario.contrasena = nueva  # Aquí deberías aplicar hash si lo deseas
                messages.success(request, 'Tu perfil y contraseña han sido actualizados correctamente.')
            else:
                messages.success(request, 'Tu perfil ha sido actualizado correctamente.')

            # Si hay foto nueva
            if 'foto_perfil' in request.FILES:
                usuario.foto_perfil = request.FILES['foto_perfil']

            usuario.save()
            return redirect('usuarios:edit_profile')
        else:
            messages.error(request, 'Corrige los errores en el formulario.')
    else:
        form = UserProfileForm(instance=usuario)

    return render(request, 'usuarios/edit_profile.html', {
        'form': form,
        'usuario': usuario,
        'title': 'Editar Perfil',
        'MEDIA_URL': settings.MEDIA_URL
    })
