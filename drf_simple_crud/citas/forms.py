# citas/forms.py
from django import forms
from django.core.exceptions import ValidationError
from datetime import date, time
from .models import Cita
from dispositivos.models import Dispositivo
from usuarios.models import Usuarios


class CitaForm(forms.ModelForm):
    tipo_servicio = forms.ChoiceField(
        choices=[('Limpieza', 'Limpieza'), ('Reparación', 'Reparación')],
        label='Tipo de servicio',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control','placeholder': 'Observaciones adicionales (opcional) - Máximo 400 caracteres','maxlength': '400','oninput': 'contarCaracteresObservaciones(this)'}),
        required=False,
        label='Observaciones',
        max_length=400
    )

    class Meta:
        model = Cita
        fields = ['asesor', 'dispositivo', 'fecha_cita', 'hora_cita', 'tipo_servicio', 'observaciones']
        widgets = {
            'fecha_cita': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': ''  # Se establecerá via JavaScript
            }),
            'hora_cita': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'min': '08:00',
                'max': '14:00'
            }),
            'asesor': forms.Select(attrs={'class': 'form-select'}),
            'dispositivo': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Mostrar solo asesores (id_rol=2)
        self.fields['asesor'].queryset = Usuarios.objects.filter(id_rol__idrol=2)

        # ✅ CAMBIO: Texto para seleccionar asesor
        self.fields['asesor'].empty_label = "Selecciona un asesor"
        self.fields['asesor'].label = "Asesor"

        # Filtrar dispositivos del usuario
        if request and hasattr(request.user, 'perfil_usuarios'):
            cliente_obj = request.user.perfil_usuarios
            self.fields['dispositivo'].queryset = Dispositivo.objects.filter(
                cliente=cliente_obj
            )
            print(f"DEBUG: Filtrando dispositivos para cliente: {cliente_obj}")
            print(f"DEBUG: Dispositivos encontrados: {self.fields['dispositivo'].queryset.count()}")
        else:
            self.fields['dispositivo'].queryset = Dispositivo.objects.none()
            print("DEBUG: No se encontró perfil_usuarios")

        self.fields['dispositivo'].empty_label = "Selecciona un dispositivo"

    def clean_fecha_cita(self):
        """Validación de fecha"""
        fecha = self.cleaned_data.get('fecha_cita')
        print(f"🔍 Validando fecha: {fecha}")

        if fecha:
            hoy = date.today()
            print(f"🔍 Hoy es: {hoy}")

            # No fechas pasadas
            if fecha < hoy:
                raise ValidationError('No se pueden agendar citas en fechas pasadas.')

            # No mismo día
            if fecha == hoy:
                raise ValidationError('Las citas deben agendarse con al menos un día de anticipación.')

            # Verificar si ya existe una cita en esa fecha
            if Cita.objects.filter(fecha_cita=fecha).exists():
                raise ValidationError('Ya existe una cita agendada para esta fecha. Por favor selecciona otra fecha.')

        return fecha

    def clean_hora_cita(self):
        """Validación de hora"""
        hora = self.cleaned_data.get('hora_cita')
        print(f"🔍 Validando hora: {hora}")

        if hora:
            hora_inicio = time(8, 0)  # 8:00 AM
            hora_fin = time(14, 0)  # 2:00 PM

            if not (hora_inicio <= hora <= hora_fin):
                raise ValidationError(
                    f'El horario debe estar entre {hora_inicio.strftime("%I:%M %p")} y {hora_fin.strftime("%I:%M %p")}'
                )

        return hora

    def clean(self):
        """Validación general del formulario"""
        cleaned_data = super().clean()
        print("🔍 Validación general del formulario")
        print(f"🔍 Datos limpios: {cleaned_data}")
        return cleaned_data