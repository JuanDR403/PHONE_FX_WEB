from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Rol(models.Model):
    idrol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre or f"Rol {self.idrol}"

    class Meta:
        db_table = 'rol'


class Usuarios(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='perfil_usuarios')
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    correo = models.CharField(unique=True, max_length=50)
    contrasena = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)

    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    id_rol = models.ForeignKey(
        Rol,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_rol',
        related_name='usuarios'
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}" if self.nombre else f"Usuario {self.iduser}"

    class Meta:
        db_table = 'usuarios'


class RegistroPerfil(models.Model):
    id = models.BigAutoField(primary_key=True)
    telefono = models.CharField(max_length=20)
    user = models.OneToOneField(Usuarios, on_delete=models.CASCADE)

    def __str__(self):
        return f"Perfil de {self.user.nombre}"

    class Meta:
        db_table = 'registro_perfil'


class UsuariosProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    profile_photo = models.CharField(max_length=100, blank=True, null=True)
    user = models.OneToOneField(Usuarios, on_delete=models.CASCADE)

    def __str__(self):
        return f"Foto de perfil de {self.user.nombre}"

    class Meta:
        db_table = 'usuarios_profile'
