from django import forms
from usuarios.models import Usuarios, Rol
from django.contrib.auth.models import User
import re





class RegistroUsuariosForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingresa una contraseña segura'}),
        help_text="Mínimo 8 caracteres con letras y números"
    )

    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirma tu contraseña'})
    )

    class Meta:
        model = Usuarios
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'direccion', 'password', 'confirmar_password']

        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ingresa tu nombre'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Ingresa tu apellido'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'Ingresa tu correo'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ingresa tu teléfono'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Ingresa tu dirección'}),
        }

    def clean_correo(self):
        correo = self.cleaned_data.get('correo').lower().strip()
        if Usuarios.objects.filter(correo=correo).exists() or User.objects.filter(username=correo).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        telefono_limpio = re.sub(r'[^\d]', '', telefono)
        if len(telefono_limpio) < 9:
            raise forms.ValidationError("El número debe tener al menos 9 dígitos.")
        return telefono_limpio

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[a-zA-Z]', password):
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres y contener letras y números.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar = cleaned_data.get("confirmar_password")
        if password and confirmar and password != confirmar:
            self.add_error('confirmar_password', "Las contraseñas no coinciden.")

    def save(self, commit=True):
        usuario = super().save(commit=False)

        # Crear el usuario base de Django
        correo = self.cleaned_data['correo']
        password = self.cleaned_data['password']
        user_base = User.objects.create(username=correo, email=correo)
        user_base.set_password(password)
        user_base.save()

        # Asignar el User al perfil extendido
        usuario.user = user_base

        # Asignar rol por defecto
        rol_cliente, _ = Rol.objects.get_or_create(nombre='cliente')
        usuario.id_rol = rol_cliente

        if commit:
            usuario.save()
        return usuario

