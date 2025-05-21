from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
from .models import PasswordResetCode
import logging

# Nuevas importaciones para la vista de página HTML
from django.shortcuts import render
from django.views import View

# Configuración de logger
logger = logging.getLogger(__name__)
User = get_user_model()


class PasswordResetRequestView(APIView):
    """
    Vista para solicitar código de recuperación (API)
    """

    def post(self, request):
        email = request.data.get('email', '').strip().lower()

        # Validación básica
        if not email:
            logger.warning('Intento de reset sin email')
            return Response(
                {"error": "El campo email es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevenir abuso
        cache_key = f"reset_attempt_{email}"
        if cache.get(cache_key):
            logger.warning(f'Intento repetido para {email}')
            return Response(
                {"error": "Espere 5 minutos antes de solicitar otro código"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        try:
            user = User.objects.get(email=email)

            # Invalidar códigos previos
            PasswordResetCode.objects.filter(user=user).update(is_used=True)

            # Crear nuevo código
            reset_code = PasswordResetCode.objects.create(user=user)

            # Enviar email
            self._send_reset_email(user, reset_code.code)

            # Registrar intento
            cache.set(cache_key, True, timeout=300)  # Bloqueo por 5 minutos

            logger.info(f'Código enviado a {email}')
            return Response(
                {
                    "success": f"Código enviado. Válido por {settings.PASSWORD_RESET['CODE_TIMEOUT']} minutos",
                    "code": str(reset_code.code)  # Solo para desarrollo
                },
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            logger.warning(f'Email no registrado: {email}')
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

    def _send_reset_email(self, user, code):
        """Envía el email con el código de recuperación"""
        subject = "Recuperación de contraseña - PhoneFX"
        context = {
            'user': user,
            'code': code,
            'expiry_minutes': settings.PASSWORD_RESET['CODE_TIMEOUT']
        }

        try:
            send_mail(
                subject=subject,
                message="",  # Versión texto plano
                html_message=render_to_string('reset_password/email_template.html', context),
                from_email=settings.PASSWORD_RESET['EMAIL_FROM'],
                recipient_list=[user.email],
                fail_silently=False
            )
        except Exception as e:
            logger.error(f'Error enviando email a {user.email}: {str(e)}')
            raise


class PasswordResetVerifyView(APIView):
    """
    Vista para verificar código y actualizar contraseña (API)
    """

    def post(self, request):
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        # Validación básica
        if not code or not new_password:
            return Response(
                {"error": "Se requieren código y nueva contraseña"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {"error": "La contraseña debe tener al menos 8 caracteres"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            reset_code = PasswordResetCode.objects.get(
                code=code,
                is_used=False
            )

            # Verificar expiración
            if reset_code.is_expired:
                reset_code.is_used = True
                reset_code.save()
                logger.warning(f'Código expirado: {code}')
                return Response(
                    {"error": "El código ha expirado"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Actualizar contraseña
            user = reset_code.user
            user.set_password(new_password)
            user.save()

            # Invalidar código
            reset_code.is_used = True
            reset_code.save()

            logger.info(f'Contraseña actualizada para {user.email}')
            return Response(
                {"success": "Contraseña actualizada correctamente"},
                status=status.HTTP_200_OK
            )

        except PasswordResetCode.DoesNotExist:
            logger.warning(f'Código inválido: {code}')
            return Response(
                {"error": "Código inválido o ya utilizado"},
                status=status.HTTP_400_BAD_REQUEST
            )

# --- Nueva vista para la página de solicitud de reseteo de contraseña ---
class PasswordResetRequestPageView(View):
    """
    Vista para mostrar la página de solicitud de reseteo de contraseña.
    """
    template_name = 'reset_password/request_reset_page.html' # Deberás crear este archivo HTML

    def get(self, request, *args, **kwargs):
        # Simplemente muestra la página con el formulario
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip().lower()
        context = {} # Contexto para pasar a la plantilla

        if not email:
            context['error_message'] = "El campo email es requerido."
            return render(request, self.template_name, context, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"reset_attempt_{email}"
        if cache.get(cache_key):
            context['error_message'] = "Espere 5 minutos antes de solicitar otro código."
            return render(request, self.template_name, context, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            user = User.objects.get(email=email)

            PasswordResetCode.objects.filter(user=user).update(is_used=True)
            reset_code_obj = PasswordResetCode.objects.create(user=user)

            # Lógica para enviar el email (similar a _send_reset_email)
            email_subject = "Recuperación de contraseña - PhoneFX"
            email_context = {
                'user': user,
                'code': reset_code_obj.code,
                'expiry_minutes': settings.PASSWORD_RESET['CODE_TIMEOUT']
            }
            try:
                send_mail(
                    subject=email_subject,
                    message="", # Puedes generar un mensaje de texto plano aquí si lo deseas
                    html_message=render_to_string('reset_password/email_template.html', email_context),
                    from_email=settings.PASSWORD_RESET['EMAIL_FROM'],
                    recipient_list=[user.email],
                    fail_silently=False
                )
                logger.info(f'Código enviado a {email} (desde página web)')
                cache.set(cache_key, True, timeout=300)
                context['success_message'] = (
                    f"Se ha enviado un código de recuperación a su correo electrónico. "
                    f"El código es válido por {settings.PASSWORD_RESET['CODE_TIMEOUT']} minutos."
                )
                # Opcionalmente, puedes mostrar el código en la página solo para desarrollo:
                # context['reset_code_for_dev'] = reset_code_obj.code
            except Exception as e:
                logger.error(f'Error enviando email a {user.email} (desde página web): {str(e)}')
                context['error_message'] = "Hubo un error al enviar el correo. Por favor, inténtelo de nuevo más tarde."
                return render(request, self.template_name, context, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return render(request, self.template_name, context)

        except User.DoesNotExist:
            # Por seguridad, usualmente no se revela si el email existe o no.
            # Se puede mostrar un mensaje genérico.
            logger.warning(f'Intento de reseteo para email no registrado (desde página web): {email}')
            context['success_message'] = ( # Mensaje genérico aunque el usuario no exista
                f"Si una cuenta con el email {email} existe, se habrá enviado un código de recuperación. "
                f"El código es válido por {settings.PASSWORD_RESET['CODE_TIMEOUT']} minutos."
            )
            # No establezcas el cache_key aquí para no dar pistas si el usuario existe.
            return render(request, self.template_name, context)
        except Exception as e:
            logger.error(f'Error inesperado en solicitud de reseteo (página web) para {email}: {str(e)}')
            context['error_message'] = "Ocurrió un error inesperado. Por favor, inténtelo de nuevo."
            return render(request, self.template_name, context, status=status.HTTP_500_INTERNAL_SERVER_ERROR)