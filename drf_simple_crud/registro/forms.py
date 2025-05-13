from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil

class RegistroForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nombre(s)",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder':'Ingresa Tu(s) Nombre(s)'}))
    
    last_name = forms.CharField(
        label="Apellido(s)",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder':'Ingresa Tu(s) Apellido(s)'}))
    
    email = forms.EmailField(
        label="Correo Electronico",
        max_length=40,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder':'Ingresa tu Correo Electrónico'}))
    
    telefono = forms.CharField(
        label="Número de Telefono",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder':'Ingresa tu numero de teléfono'}))

    password1 = forms.CharField(
        label="contraseña1",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder':'Ingresa una contraseña'})
    )
    password2 = forms.CharField(
        label="contraseña2",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder':'Confirme su contraseña'})
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
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono.isdigit():
            raise forms.ValidationError("El número de teléfono solo debe contener dígitos.")
        if len(telefono) < 9:
            raise forms.ValidationError("El número de teléfono debe tener al menos 9 dígitos.")
        return telefono

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1 and password1.isdigit():
            raise forms.ValidationError('La contraseña no puede contener solo números.')
        if len(password1) < 8:
            raise forms.ValidationError('La contraseña tiene que tener mínimo 8 caracteres.')
        return password1 # Asegúrate de devolver el valor limpio

    def clean_password2(self): # Corregido el nombre del metodo
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2: # Asegurarse que password1 y password2 no son None
         raise forms.ValidationError('Las contraseñas no coinciden.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        base_username = f"{self.cleaned_data['first_name'].lower()}_{self.cleaned_data['last_name'].lower()}"
        username = base_username
        counter = 1
    
        # Asegura que el username sea único
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
    
        user.username = username  # Asigna el username generado
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            perfil, created = Perfil.objects.get_or_create(user=user)
            perfil.telefono = self.cleaned_data['telefono']
            perfil.save()
            
        return user