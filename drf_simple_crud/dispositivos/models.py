from django.db import models
from usuarios.models import Usuarios


class Dispositivo(models.Model):
    iddispositivo = models.AutoField(db_column='idDispositivo', primary_key=True)

    cliente = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_cliente',
        related_name='dispositivos'
    )

    marca = models.CharField(max_length=8, blank=True, null=True)
    modelo = models.CharField(max_length=50, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.CharField(max_length=45)

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.numero_serie}"

    class Meta:
        db_table = 'dispositivo'
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
