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
    ESTADOS = [
        ('pendiente', 'Solicitud'),
        ('en proceso', 'En Proceso'),
        ('finalizado', 'Finalizado'),
        ('olvidado', 'Olvidado'),
    ]

    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Cita #{self.idcita} - {self.fecha_cita} {self.hora_cita}"

    class Meta:
        db_table = 'cita'


class HistorialCita(models.Model):
    ESTADOS = [
        ('Solicitud', 'Solicitud'),
        ('En Proceso', 'En Proceso'),
        ('Finalizado', 'Finalizado'),
        ('Olvidado', 'Olvidado'),
    ]

    idhistorial = models.AutoField(db_column='idHistorial', primary_key=True)

    cita = models.ForeignKey(
        Cita,
        on_delete=models.CASCADE,
        db_column='idCita',
        related_name='historiales'
    )

    estado_anterior = models.CharField(
        max_length=20,
        choices=ESTADOS,
        db_column='estado_anterior'
    )

    estado_nuevo = models.CharField(
        max_length=20,
        choices=ESTADOS,
        db_column='estado_nuevo'
    )

    fecha_cambio = models.DateTimeField(
        auto_now_add=True,
        db_column='fecha_cambio'
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        db_column='observaciones'
    )

    def __str__(self):
        return f"Historial #{self.idhistorial} - Cita {self.cita.idcita} ({self.estado_anterior} → {self.estado_nuevo})"

    class Meta:
        managed = False
        db_table = 'historial_cita'