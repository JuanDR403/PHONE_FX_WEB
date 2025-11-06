from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Rol, Usuarios

@receiver(post_migrate)
def crear_roles_y_usuarios_iniciales(sender, **kwargs):
    if sender.name == 'usuarios':  # 👈 asegura que solo se ejecute para esta app

        # 1️⃣ Crear roles base
        roles_data = [
            (1, 'cliente', 'Rol para clientes del sistema'),
            (2, 'asesor', 'Rol para asesores técnicos'),
            (3, 'admin', 'Rol para administradores del sistema'),
        ]

        for idrol, nombre, descripcion in roles_data:
            Rol.objects.get_or_create(
                idrol=idrol,
                defaults={'nombre': nombre, 'descripcion': descripcion}
            )

        # 2️⃣ Crear usuarios base si no existen
        usuarios_data = [
            {
                "username": "admin",
                "email": "admin@phonefx.com",
                "password": "admin123",
                "first_name": "Administrador",
                "last_name": "Principal",
                "rol_nombre": "admin",
            },
            {
                "username": "asesor",
                "email": "asesor@phonefx.com",
                "password": "asesor123",
                "first_name": "Asesor",
                "last_name": "Técnico",
                "rol_nombre": "asesor",
            },
            {
                "username": "cliente",
                "email": "cliente@phonefx.com",
                "password": "cliente123",
                "first_name": "Cliente",
                "last_name": "General",
                "rol_nombre": "cliente",
            },
        ]

        for datos in usuarios_data:
            rol = Rol.objects.get(nombre=datos["rol_nombre"])

            # Crea el usuario de Django (User)
            user, creado = User.objects.get_or_create(
                username=datos["username"],
                defaults={
                    "email": datos["email"],
                    "first_name": datos["first_name"],
                    "last_name": datos["last_name"],
                }
            )

            if creado:
                user.set_password(datos["password"])
                user.save()

                # Crea su perfil en Usuarios
                Usuarios.objects.create(
                    user=user,
                    nombre=datos["first_name"],
                    apellido=datos["last_name"],
                    correo=datos["email"],
                    contrasena=datos["password"],  # opcional, solo para reflejar en tu modelo
                    id_rol=rol,
                )
