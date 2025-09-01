from django import forms
from usuarios.models import Usuarios
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from usuarios.models import UsuariosProfile


class ProfilePhotoForm(forms.ModelForm):
    photo = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UsuariosProfile
        fields = []


class UserProfileForm(forms.ModelForm):
    new_password = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    confirm_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Usuarios
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password or confirm_password:
            if new_password != confirm_password:
                self.add_error('confirm_password', 'Las contraseñas no coinciden.')
            else:
                try:
                    validate_password(new_password)
                except ValidationError as e:
                    self.add_error('new_password', e)

        return cleaned_data