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

# Configuración de logger
logger = logging.getLogger(__name__)
User = get_user_model()


class PasswordResetRequestView(APIView):
    """
    Vista para solicitar código de recuperación
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
    Vista para verificar código y actualizar contraseña
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