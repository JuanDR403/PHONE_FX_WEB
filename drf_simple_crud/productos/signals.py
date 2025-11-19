from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Categoria


@receiver(post_migrate)
def crear_categorias_iniciales(sender, **kwargs):
    if sender.name == 'productos':  # 👈 Cambia a 'productos'

        categorias_data = [
            (1, 'Forros', 'Forros y fundas protectoras para celulares'),
            (2, 'Vidrios', 'Vidrios templados y protectores de pantalla'),
            (3, 'Celulares', 'Teléfonos móviles y smartphones'),
            (4, 'Audifonos', 'Auriculares y audífonos para dispositivos móviles'),
            (5, 'Cargadores', 'Cargadores y adaptadores de corriente'),
            (6, 'Cables', 'Cables de datos y carga para dispositivos móviles'),
        ]

        for idcategoria, nombre, descripcion in categorias_data:
            Categoria.objects.get_or_create(
                idcategoria=idcategoria,
                defaults={'nombre': nombre, 'descripcion': descripcion}
            )