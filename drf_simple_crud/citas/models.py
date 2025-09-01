from django.db import models
from usuarios.models import Usuarios
from dispositivos.models import Dispositivo


class Cita(models.Model):
    idcita = models.AutoField(db_column='idCita', primary_key=True)

    cliente = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_cliente',
        related_name='citas_como_cliente'
    )

    asesor = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_asesor',
        related_name='citas_como_asesor'
    )

    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.SET_NULL,
        null=True,
        db_column='id_dispositivo',
        related_name='citas'
    )

    fecha_cita = models.CharField(max_length=50)
    hora_cita = models.CharField(max_length=45)
    tipo_servicio = models.CharField(max_length=10)
    estado = models.CharField(max_length=10)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Cita #{self.idcita} - {self.fecha_cita} {self.hora_cita}"

    class Meta:
        db_table = 'cita'
