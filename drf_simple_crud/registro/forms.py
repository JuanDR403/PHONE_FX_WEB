from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil
import re



class RegistroForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nombre(s)",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ingresa Tu(s) Nombre(s)'}))

    last_name = forms.CharField(
        label="Apellido(s)",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ingresa Tu(s) Apellido(s)'}))

    email = forms.EmailField(
        label="Correo Electrónico",
        max_length=254,  # Longitud máxima estándar para emails
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Ingresa tu Correo Electrónico',
            'autocomplete': 'email'
        }))

    telefono = forms.CharField(
        label="Número de Teléfono",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ingresa tu número de teléfono',
            'pattern': '[0-9]+',  # HTML5 validation
            'title': 'Solo números permitidos'
        }))

    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Ingresa una contraseña segura',
            'autocomplete': 'new-password'
        }),
        help_text="Mínimo 8 caracteres con letras y números"
    )

    password2 = forms.CharField(
        label="Confirmación de contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirma tu contraseña',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'telefono',
            'password1',
            'password2'
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        telefono_limpio = re.sub(r'[^\d]', '', telefono)  # Elimina todo excepto dígitos

        if len(telefono_limpio) < 9:
            raise forms.ValidationError("El número debe tener al menos 9 dígitos.")
        return telefono_limpio

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r'\d', password1) or not re.search(r'[a-zA-Z]', password1):
            raise forms.ValidationError("La contraseña debe contener letras y números.")
        return password1

    def save(self, commit=True):
        user = super().save(commit=False)
        # Normaliza el email
        user.email = self.cleaned_data['email'].lower().strip()

        # Genera username único
        base_username = f"{self.cleaned_data['first_name'].lower()}_{self.cleaned_data['last_name'].lower()}"
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user.username = username

        if commit:
            user.save()
            # Asegura que set_password se llama (heredado de UserCreationForm)
            Perfil.objects.update_or_create(
                user=user,
                defaults={'telefono': self.cleaned_data['telefono']}
            )

        return user