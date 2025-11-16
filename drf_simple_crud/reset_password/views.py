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
from django.contrib import messages
from django.shortcuts import redirect

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
    template_name = 'reset_password/request_reset_page.html'

    def get(self, request, *args, **kwargs):
        # Simplemente muestra la página con el formulario
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '').strip().lower()
        context = {}

        if not email:
            context['error_message'] = "El campo email es requerido."
            return render(request, self.template_name, context, status=400)

        cache_key = f"reset_attempt_{email}"
        if cache.get(cache_key):
            context['error_message'] = "Espere 5 minutos antes de solicitar otro código."
            return render(request, self.template_name, context, status=429)

        try:
            user = User.objects.get(email=email)

            PasswordResetCode.objects.filter(user=user).update(is_used=True)
            reset_code_obj = PasswordResetCode.objects.create(user=user)

            # Lógica para enviar el email
            email_subject = "Recuperación de contraseña - PhoneFX"
            email_context = {
                'user': user,
                'code': reset_code_obj.code,
                'expiry_minutes': settings.PASSWORD_RESET['CODE_TIMEOUT']
            }

            try:
                send_mail(
                    subject=email_subject,
                    message="",
                    html_message=render_to_string('reset_password/email_template.html', email_context),
                    from_email=settings.PASSWORD_RESET['EMAIL_FROM'],
                    recipient_list=[user.email],
                    fail_silently=False
                )
                logger.info(f'Código enviado a {email} (desde página web)')
                cache.set(cache_key, True, timeout=300)

                # REDIRECCIÓN AUTOMÁTICA en lugar de mostrar mensaje
                messages.success(request,
                                 f"Se ha enviado un código de recuperación a su correo electrónico. "
                                 f"El código es válido por {settings.PASSWORD_RESET['CODE_TIMEOUT']} minutos."
                                 )
                return redirect('reset_password:verify_code')  # Redirección automática

            except Exception as e:
                logger.error(f'Error enviando email a {user.email} (desde página web): {str(e)}')
                context['error_message'] = "Hubo un error al enviar el correo. Por favor, inténtelo de nuevo más tarde."
                return render(request, self.template_name, context, status=500)

        except User.DoesNotExist:
            # Por seguridad, mostramos mensaje genérico pero NO redireccionamos
            logger.warning(f'Intento de reseteo para email no registrado (desde página web): {email}')
            context['success_message'] = (
                f"Si una cuenta con el email {email} existe, se habrá enviado un código de recuperación. "
                f"El código es válido por {settings.PASSWORD_RESET['CODE_TIMEOUT']} minutos."
            )
            return render(request, self.template_name, context)
        except Exception as e:
            logger.error(f'Error inesperado en solicitud de reseteo (página web) para {email}: {str(e)}')
            context['error_message'] = "Ocurrió un error inesperado. Por favor, inténtelo de nuevo."
            return render(request, self.template_name, context, status=500)


class PasswordResetVerifyPageView(View):
    """
    Vista para mostrar y procesar la página de verificación de código
    """
    template_name = 'reset_password/verify_code.html'

    def get(self, request, *args, **kwargs):
        # Mostrar el formulario de verificación
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        code = request.POST.get('code', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validaciones básicas
        if not code or not new_password or not confirm_password:
            messages.error(request, "Todos los campos son requeridos")
            return render(request, self.template_name, status=400)

        if new_password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, self.template_name, status=400)

        if len(new_password) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres")
            return render(request, self.template_name, status=400)

        try:
            # Buscar el código no utilizado
            reset_code = PasswordResetCode.objects.get(
                code=code,
                is_used=False
            )

            # Verificar si ha expirado
            if reset_code.is_expired:
                reset_code.is_used = True
                reset_code.save()
                messages.error(request, "El código ha expirado. Por favor, solicita uno nuevo.")
                return render(request, self.template_name, status=400)

            # Actualizar la contraseña del usuario
            user = reset_code.user
            user.set_password(new_password)
            user.save()

            # Marcar el código como utilizado
            reset_code.is_used = True
            reset_code.save()

            logger.info(f'Contraseña actualizada exitosamente para {user.email} (desde página web)')
            messages.success(request,
                             "¡Contraseña actualizada correctamente! Ya puedes iniciar sesión con tu nueva contraseña.")

            # Redirigir al login
            return redirect('logueo:login')  # Cambia por el nombre de tu URL de login

        except PasswordResetCode.DoesNotExist:
            logger.warning(f'Código inválido intentado (desde página web): {code}')
            messages.error(request, "Código inválido o ya utilizado")
            return render(request, self.template_name, status=400)
        except Exception as e:
            logger.error(f'Error inesperado en verificación de código (página web): {str(e)}')
            messages.error(request, "Ocurrió un error inesperado. Por favor, inténtalo de nuevo.")
            return render(request, self.template_name, status=500)