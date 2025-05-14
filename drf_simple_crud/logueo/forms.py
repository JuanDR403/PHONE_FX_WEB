from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Correo Electrónico o Nombre de Usuario",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@dominio.com o nombre de usuario',
            'autocomplete': 'username',
            'autocapitalize': 'none'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña',
            'autocomplete': 'current-password'
        })
    )

    error_messages = {
        'invalid_login': "Credenciales incorrectas. Verifique su nombre de usuario o correo y contraseña.",
        'inactive': "Esta cuenta está inactiva. Contacte al administrador.",
        'invalid_credentials': "Este usuario o correo no está registrado.",
    }

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email is not None and password:
            # Normaliza la entrada (minúsculas, sin espacios)
            username_or_email = username_or_email.lower().strip()

            # Determina si es un correo o un nombre de usuario
            is_email = '@' in username_or_email

            self.user_cache = authenticate(
                self.request,
                username=username_or_email,
                password=password
            )

            if self.user_cache is None:
                # Verifica si el usuario o correo existe para dar feedback más específico
                if is_email:
                    user_exists = User.objects.filter(email=username_or_email).exists()
                else:
                    user_exists = User.objects.filter(username=username_or_email).exists()

                if user_exists:
                    raise ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                    )
                else:
                    raise ValidationError(
                        self.error_messages['invalid_credentials'],
                        code='invalid_credentials',
                    )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
