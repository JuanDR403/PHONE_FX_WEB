from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time, datetime
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

    fecha_cita = models.DateField()  # ✅ campo tipo fecha
    hora_cita = models.TimeField()
    tipo_servicio = models.CharField(max_length=10)
    ESTADOS = [
        ('pendiente', 'Solicitud'),
        ('en proceso', 'En Proceso'),
        ('finalizado', 'Finalizado'),
        ('olvidado', 'Olvidado'),
    ]

    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    observaciones = models.TextField(blank=True, null=True)

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()

        # Validación 1: No fechas pasadas ni del día actual
        if self.fecha_cita:
            hoy = date.today()

            if self.fecha_cita < hoy:
                raise ValidationError({
                    'fecha_cita': 'No se pueden agendar citas en fechas pasadas.'
                })

            if self.fecha_cita == hoy:
                raise ValidationError({
                    'fecha_cita': 'Las citas deben agendarse con al menos un día de anticipación.'
                })

        # Validación 2: No misma fecha (día completo)
        if self.fecha_cita and self.idcita:  # Si es una actualización
            citas_mismo_dia = Cita.objects.filter(
                fecha_cita=self.fecha_cita
            ).exclude(idcita=self.idcita)
        elif self.fecha_cita:  # Si es una creación nueva
            citas_mismo_dia = Cita.objects.filter(fecha_cita=self.fecha_cita)

        if self.fecha_cita and citas_mismo_dia.exists():
            raise ValidationError({
                'fecha_cita': 'Ya existe una cita agendada para esta fecha. Por favor selecciona otra fecha.'
            })

        # Validación 3: Horario permitido (8:00 AM - 2:00 PM)
        if self.hora_cita:
            hora_inicio = time(8, 0)  # 8:00 AM
            hora_fin = time(14, 0)  # 2:00 PM

            if not (hora_inicio <= self.hora_cita <= hora_fin):
                raise ValidationError({
                    'hora_cita': f'El horario debe estar entre {hora_inicio.strftime("%I:%M %p")} y {hora_fin.strftime("%I:%M %p")}'
                })

    def save(self, *args, **kwargs):
        """Ejecutar validaciones antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)

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
        managed = True
        db_table = 'historial_cita'