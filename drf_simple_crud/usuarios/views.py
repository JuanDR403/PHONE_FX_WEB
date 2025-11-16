from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from usuarios.models import Usuarios
from .forms import UserProfileForm
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
import uuid
import logging

logger = logging.getLogger(__name__)


@login_required
def edit_profile(request):
    try:
        usuario = Usuarios.objects.get(user=request.user)
    except Usuarios.DoesNotExist:
        messages.error(request, "No se encontró el usuario.")
        return redirect('inicio:home')

    if request.method == 'POST':
        # =============================================
        # 1. SUBIR FOTO DE PERFIL
        # =============================================
        if request.POST.get('photo_form_submitted') == '1' and 'foto_perfil' in request.FILES:
            usuario.foto_perfil = request.FILES['foto_perfil']
            usuario.save()
            messages.success(request, 'Tu foto de perfil ha sido actualizada correctamente.')
            return redirect('usuarios:edit_profile')

        # =============================================
        # 2. SOLICITAR CÓDIGO DE VERIFICACIÓN
        # =============================================
        elif request.POST.get('send_verification_code') == '1':
            send_verification_code(request, usuario)
            # Siempre redirigir para mostrar mensajes
            return redirect('usuarios:edit_profile')

        # =============================================
        # 3. VERIFICAR CÓDIGO Y CAMBIAR CONTRASEÑA
        # =============================================
        elif request.POST.get('verify_code_and_change') == '1':
            return verify_code_and_change_password(request, usuario)

        # =============================================
        # 4. ACTUALIZAR DATOS DEL PERFIL (sin contraseña)
        # =============================================
        else:
            form = UserProfileForm(request.POST, request.FILES, instance=usuario)

            # Validación de correo duplicado
            correo = request.POST.get('correo')
            if correo and Usuarios.objects.filter(correo=correo).exclude(pk=usuario.pk).exists():
                messages.error(request, 'Este correo electrónico ya está registrado.')
                return render(request, 'usuarios/edit_profile.html', {
                    'form': form,
                    'usuario': usuario,
                    'title': 'Editar Perfil',
                    'MEDIA_URL': settings.MEDIA_URL
                })

            if form.is_valid():
                usuario = form.save(commit=False)

                # Guardar sin cambiar contraseña (la contraseña se cambia con verificación)
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


def send_verification_code(request, usuario):
    """Envía código de verificación para cambiar contraseña"""
    cache_key = f"password_change_attempt_{usuario.correo}"

    # Prevenir abuso
    if cache.get(cache_key):
        messages.error(request, "Espere 5 minutos antes de solicitar otro código.")
        return

    # Generar código único
    verification_code = str(uuid.uuid4())[:8].upper()

    # Guardar código en cache (válido por 8 minutos)
    cache.set(f"password_change_code_{usuario.correo}", verification_code, 480)
    cache.set(cache_key, True, 300)  # Bloqueo por 5 minutos

    # Enviar email
    try:
        subject = "Código de verificación - Cambio de contraseña - PhoneFX"
        context = {
            'user': usuario,
            'code': verification_code,
            'expiry_minutes': 8
        }

        send_mail(
            subject=subject,
            message="",
            html_message=render_to_string('reset_password/email_template.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.correo],
            fail_silently=False
        )

        logger.info(f'Código de verificación enviado a {usuario.correo} para cambio de contraseña')
        messages.success(request, f'Se ha enviado un código de verificación a tu correo. Válido por 8 minutos.')

    except Exception as e:
        logger.error(f'Error enviando código de verificación a {usuario.correo}: {str(e)}')
        messages.error(request, 'Error al enviar el código. Inténtalo de nuevo.')


def verify_code_and_change_password(request, usuario):
    """Verifica el código y cambia la contraseña"""
    entered_code = request.POST.get('verification_code', '').strip().upper()
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    # Validaciones básicas
    if not entered_code or not new_password or not confirm_password:
        messages.error(request, 'Todos los campos son requeridos.')
        return redirect('usuarios:edit_profile')

    if new_password != confirm_password:
        messages.error(request, 'Las contraseñas no coinciden.')
        return redirect('usuarios:edit_profile')

    if len(new_password) < 8:
        messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
        return redirect('usuarios:edit_profile')

    # Verificar que la nueva contraseña no sea igual a la anterior
    try:
        if check_password(new_password, usuario.contrasena):
            messages.error(request, 'La nueva contraseña no puede ser igual a la anterior.')
            return redirect('usuarios:edit_profile')
    except Exception as e:
        # Si hay algún error en la verificación, continuar
        logger.warning(f'No se pudo verificar contraseña anterior: {e}')

    # Verificar código
    stored_code = cache.get(f"password_change_code_{usuario.correo}")

    if not stored_code:
        messages.error(request, 'El código ha expirado o no existe. Solicita uno nuevo.')
        return redirect('usuarios:edit_profile')

    if entered_code != stored_code:
        messages.error(request, 'Código de verificación incorrecto.')
        return redirect('usuarios:edit_profile')

    # Código correcto - cambiar contraseña
    try:
        # Actualizar contraseña en el modelo Usuarios
        usuario.contrasena = make_password(new_password)
        usuario.save()

        # También actualizar contraseña del usuario de Django
        user = request.user
        user.set_password(new_password)
        user.save()

        # Invalidar código usado
        cache.delete(f"password_change_code_{usuario.correo}")

        logger.info(f'Contraseña cambiada exitosamente para {usuario.correo}')
        messages.success(request, '¡Contraseña cambiada exitosamente!')

    except Exception as e:
        logger.error(f'Error cambiando contraseña para {usuario.correo}: {str(e)}')
        messages.error(request, 'Error al cambiar la contraseña. Inténtalo de nuevo.')

    return redirect('usuarios:edit_profile')