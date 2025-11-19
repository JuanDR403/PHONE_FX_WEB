from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .forms import RegistroUsuariosForm
from django.contrib.auth import login
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
from django.contrib import messages
import logging
import secrets
from datetime import timedelta
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Configuración de logger
logger = logging.getLogger(__name__)

# Importa tu modelo Usuarios si lo tienes
# from .models import Usuarios
from django.contrib.auth import get_user_model

User = get_user_model()

# Modelo para almacenar códigos de verificación
from django.db import models


class EmailVerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    registration_data = models.JSONField(default=dict)

    @property
    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=30)
        return timezone.now() > expiration_time

    def __str__(self):
        return f"{self.email} - {self.code}"


def registro(request):
    """Vista principal de registro - mantiene funcionalidad original + verificación"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return registro_ajax(request)

    if request.method == 'POST':
        # Procesamiento tradicional (sin AJAX)
        form = RegistroUsuariosForm(request.POST)
        if form.is_valid():
            # Enviar código de verificación en lugar de crear usuario inmediatamente
            return _procesar_registro_inicial(request, form)
    else:
        form = RegistroUsuariosForm()

    return render(request, 'registro/registro.html', {'form': form})


@require_http_methods(["POST"])
def registro_ajax(request):
    """Maneja el registro inicial via AJAX y envía código de verificación"""
    try:
        form = RegistroUsuariosForm(request.POST)

        if not form.is_valid():
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'error': 'Datos del formulario inválidos',
                'details': errors
            }, status=400)

        email = form.cleaned_data['correo'].lower()

        # Verificar si el email ya está registrado
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'Este correo ya está registrado'
            }, status=400)

        # Prevenir abuso
        cache_key = f"register_attempt_{email}"
        attempt_count = cache.get(cache_key, 0)

        if attempt_count >= 3:
            return JsonResponse({
                'success': False,
                'error': 'Demasiados intentos. Espere 5 minutos antes de intentar nuevamente.'
            }, status=429)

        # Invalidar códigos previos
        EmailVerificationCode.objects.filter(email=email, is_used=False).update(is_used=True)

        # Crear código de verificación
        codigo = str(secrets.randbelow(900000) + 100000).zfill(6)

        # Guardar datos del formulario COMPLETOS para recrear el form después
        verification_code = EmailVerificationCode.objects.create(
            email=email,
            code=codigo,
            registration_data={
                'form_data': form.cleaned_data,  # Guarda todos los datos limpios del form
                'post_data': dict(request.POST)  # Guarda datos POST originales
            }
        )

        # Enviar email de verificación
        _enviar_email_verificacion(email, codigo)

        # Incrementar contador de intentos
        cache.set(cache_key, attempt_count + 1, timeout=300)

        response_data = {
            'success': True,
            'message': 'Código de verificación enviado a tu correo electrónico',
            'email': email
        }

        # Solo en desarrollo - mostrar código
        if settings.DEBUG:
            response_data['debug_code'] = codigo

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f'Error en registro AJAX: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al procesar el registro. Intente nuevamente.'
        }, status=500)


@require_http_methods(["POST"])
def verificar_registro(request):
    """Verifica el código y crea el usuario MANTENIENDO la lógica original"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)

    codigo = data.get('verification_code', '').strip()
    email = data.get('email', '')

    if not codigo or not email:
        return JsonResponse({
            'success': False,
            'error': 'Código y email requeridos'
        }, status=400)

    if len(codigo) != 6 or not codigo.isdigit():
        return JsonResponse({
            'success': False,
            'error': 'El código debe tener 6 dígitos numéricos'
        }, status=400)

    try:
        # Buscar código válido
        verification_code = EmailVerificationCode.objects.get(
            email=email,
            code=codigo,
            is_used=False
        )

        # Verificar expiración
        if verification_code.is_expired:
            verification_code.is_used = True
            verification_code.save()
            return JsonResponse({
                'success': False,
                'error': 'El código ha expirado. Por favor, solicite uno nuevo.'
            }, status=400)

        # Obtener datos del registro guardados
        registration_data = verification_code.registration_data
        form_data = registration_data['form_data']

        # Recrear el formulario con los datos originales
        form = RegistroUsuariosForm(form_data)

        if form.is_valid():
            # ✅ MANTENER LA LÓGICA ORIGINAL DE REGISTRO
            user = form.save(commit=False)  # Evita guardar inmediatamente

            # Asignar nombre y apellido al modelo User (tu lógica original)
            user.first_name = form_data.get('nombre', '')
            user.last_name = form_data.get('apellido', '')
            user.save()

            # ✅ SI TIENES MODELO Usuarios, CREARLO AQUÍ
            # Ejemplo:
            # Usuarios.objects.create(
            #     user=user,
            #     telefono=form_data.get('telefono', ''),
            #     direccion=form_data.get('direccion', ''),
            #     # ... otros campos
            # )

            # Marcar código como usado
            verification_code.is_used = True
            verification_code.save()

            # Limpiar contador de intentos
            cache_key = f"register_attempt_{email}"
            cache.delete(cache_key)

            logger.info(f'Nuevo usuario registrado: {email} - {user.first_name} {user.last_name}')

            return JsonResponse({
                'success': True,
                'message': '¡Cuenta creada exitosamente! Ya puedes iniciar sesión con tus credenciales.'
            })

        else:
            # Si el form no es válido al recrearlo
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'error': 'Error en los datos del formulario',
                'details': errors
            }, status=400)

    except EmailVerificationCode.DoesNotExist:
        logger.warning(f'Código inválido intentado para {email}: {codigo}')
        return JsonResponse({
            'success': False,
            'error': 'Código inválido. Por favor, verifique e intente nuevamente.'
        }, status=400)
    except Exception as e:
        logger.error(f'Error verificando código para {email}: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al verificar el código. Intente nuevamente.'
        }, status=500)


@require_http_methods(["POST"])
def reenviar_codigo(request):
    """Reenvía el código de verificación via AJAX"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)

    email = data.get('email', '')

    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email no proporcionado'
        }, status=400)

    try:
        # Buscar el código pendiente más reciente
        codigo_pendiente = EmailVerificationCode.objects.filter(
            email=email,
            is_used=False
        ).order_by('-created_at').first()

        if not codigo_pendiente:
            return JsonResponse({
                'success': False,
                'error': 'No hay solicitud de registro pendiente para este email'
            }, status=400)

        # Verificar si ya se reenvió recientemente
        cache_key_resend = f"resend_cooldown_{email}"
        if cache.get(cache_key_resend):
            return JsonResponse({
                'success': False,
                'error': 'Espere 1 minuto antes de solicitar otro código'
            }, status=429)

        # Invalidar código anterior y crear uno nuevo
        codigo_pendiente.is_used = True
        codigo_pendiente.save()

        nuevo_codigo = str(secrets.randbelow(900000) + 100000).zfill(6)

        EmailVerificationCode.objects.create(
            email=email,
            code=nuevo_codigo,
            registration_data=codigo_pendiente.registration_data
        )

        # Enviar nuevo email
        _enviar_email_verificacion(email, nuevo_codigo)

        # Establecer cooldown para reenvíos
        cache.set(cache_key_resend, True, timeout=60)

        response_data = {
            'success': True,
            'message': 'Se ha enviado un nuevo código a tu correo electrónico'
        }

        if settings.DEBUG:
            response_data['debug_code'] = nuevo_codigo

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f'Error reenviando código a {email}: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error al reenviar el código. Intente nuevamente.'
        }, status=500)


def _procesar_registro_inicial(request, form):
    """Función auxiliar para procesamiento tradicional (sin AJAX)"""
    email = form.cleaned_data['correo'].lower()

    if User.objects.filter(email=email).exists():
        form.add_error('correo', 'Este correo ya está registrado')
        return render(request, 'registro/registro.html', {'form': form})

    cache_key = f"register_attempt_{email}"
    attempt_count = cache.get(cache_key, 0)

    if attempt_count >= 3:
        form.add_error('correo', 'Demasiados intentos. Espere 5 minutos antes de intentar nuevamente.')
        return render(request, 'registro/registro.html', {'form': form})

    try:
        EmailVerificationCode.objects.filter(email=email, is_used=False).update(is_used=True)

        codigo = str(secrets.randbelow(900000) + 100000).zfill(6)

        EmailVerificationCode.objects.create(
            email=email,
            code=codigo,
            registration_data={
                'form_data': form.cleaned_data,
                'post_data': dict(request.POST)
            }
        )

        _enviar_email_verificacion(email, codigo)
        cache.set(cache_key, attempt_count + 1, timeout=300)

        # Para flujo tradicional, redirigir a página de verificación separada
        return render(request, 'registro/verificar_email.html', {
            'email': email,
            'codigo_debug': codigo if settings.DEBUG else None
        })

    except Exception as e:
        logger.error(f'Error en registro inicial para {email}: {str(e)}', exc_info=True)
        form.add_error('correo', 'Error al procesar el registro. Intente nuevamente.')
        return render(request, 'registro/registro.html', {'form': form})


def _enviar_email_verificacion(email, codigo):
    """Envía el email con el código de verificación"""
    subject = "Verificación de correo - PhoneFX"
    context = {
        'email': email,
        'code': codigo,
        'expiry_minutes': 30
    }

    try:
        plain_message = f"""
        Tu código de verificación para PhoneFX es: {codigo}

        Este código expirará en 30 minutos.

        Si no solicitaste este registro, por favor ignora este mensaje.

        Atentamente,
        El equipo de PhoneFX
        """

        html_message = render_to_string('registro/email_verificacion.html', context)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@phonefx.com'),
            recipient_list=[email],
            fail_silently=False
        )
        logger.info(f'Email de verificación enviado a {email}')

    except Exception as e:
        logger.error(f'Error enviando email de verificación a {email}: {str(e)}', exc_info=True)
        raise