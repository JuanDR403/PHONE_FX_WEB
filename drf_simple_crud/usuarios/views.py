from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from usuarios.models import Usuarios, UsuariosProfile
from .forms import UserProfileForm, ProfilePhotoForm
from django.conf import settings
from django.core.files.storage import FileSystemStorage
  # o desde .utils si lo moviste allí
from PIL import Image

@login_required
def edit_profile(request):


    try:
        usuario = Usuarios.objects.get(user=request.user)
    except Usuarios.DoesNotExist:
        messages.error(request, "No se encontró el perfil extendido del usuario.")
        return redirect('inicio:home')

    profile, _ = UsuariosProfile.objects.get_or_create(user=usuario)

    if request.method == 'POST':
        if 'photo_form_submitted' in request.POST:
            photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)

            if photo_form.is_valid():
                photo_instance = photo_form.save(commit=False)

                if 'profile_photo' in request.FILES:
                    photo_instance.profile_photo = compress_image(request.FILES['profile_photo'])

                photo_instance.save()

                messages.success(request, 'Tu foto de perfil ha sido actualizada correctamente.')
                return redirect('usuarios:edit_profile')
            else:
                messages.error(request, 'Hubo un error al procesar la foto de perfil.')
                form = UserProfileForm(instance=usuario)
        else:
            form = UserProfileForm(request.POST, instance=usuario)
            photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)

            correo = request.POST.get('correo')
            if Usuarios.objects.filter(correo=correo).exclude(pk=usuario.pk).exists():
                messages.error(request, 'Este correo electrónico ya está registrado.')
                return render(request, 'usuarios/edit_profile.html', {
                    'form': form,
                    'photo_form': photo_form,
                    'profile': profile,
                    'title': 'Editar Perfil'
                })

            if form.is_valid() and photo_form.is_valid():
                usuario = form.save(commit=False)
                nueva = form.cleaned_data.get('new_password')
                if nueva:
                    usuario.contrasena = nueva  # Puedes aplicar hash si lo deseas
                    messages.success(request, 'Tu perfil, contraseña y foto han sido actualizados correctamente.')
                else:
                    messages.success(request, 'Tu perfil y foto han sido actualizados correctamente.')

                usuario.save()

                if 'profile_photo' in request.FILES:
                    photo_instance = photo_form.save(commit=False)
                    photo_instance.profile_photo = compress_image(request.FILES['profile_photo'])
                    photo_instance.save()
                else:
                    photo_form.save()

                return redirect('usuarios:edit_profile')
            else:
                messages.error(request, 'Corrige los errores en el formulario.')
    else:
        form = UserProfileForm(instance=usuario)
        photo_form = ProfilePhotoForm(instance=profile)

    return render(request, 'usuarios/edit_profile.html', {
        'form': form,
        'photo_form': photo_form,
        'profile': profile,
        'usuario': usuario,
        'title': 'Editar Perfil',
        'MEDIA_URL': settings.MEDIA_URL
    })