# dispositivos/models.py
from django.db import models
from usuarios.models import Usuarios


class Dispositivo(models.Model):
    # Definir las opciones del ENUM
    MARCA_CHOICES = [
        ('Apple', 'Apple'),
        ('Samsung', 'Samsung'),
        ('Xiaomi', 'Xiaomi'),
        ('OPPO', 'OPPO'),
        ('Vivo', 'Vivo'),
        ('Huawei', 'Huawei'),
        ('Realme', 'Realme'),
        ('Honor', 'Honor'),
        ('OnePlus', 'OnePlus'),
        ('Motorola', 'Motorola'),
        ('Sony', 'Sony'),
        ('Nokia', 'Nokia'),
        ('Infinix', 'Infinix'),
        ('Tecno', 'Tecno'),
        ('Google', 'Google'),
    ]

    iddispositivo = models.AutoField(db_column='idDispositivo', primary_key=True)

    cliente = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_cliente',
        related_name='dispositivos'
    )

    marca = models.CharField(
        max_length=20,
        choices=MARCA_CHOICES,
        blank=True,
        null=True
    )
    modelo = models.CharField(max_length=50, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.numero_serie}"

    class Meta:
        db_table = 'dispositivo'
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'