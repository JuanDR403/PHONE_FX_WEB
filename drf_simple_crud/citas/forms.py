from django import forms
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
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        label='Observaciones'
    )

    class Meta:
        model = Cita
        fields = ['asesor', 'dispositivo', 'fecha_cita', 'hora_cita', 'tipo_servicio', 'observaciones']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # ✅ Mostrar solo asesores (id_rol=2)
        self.fields['asesor'].queryset = Usuarios.objects.filter(id_rol__idrol=2)

        # ✅ Filtrar solo los dispositivos del cliente autenticado
        if request and hasattr(request.user, 'perfil_usuarios'):
            self.fields['dispositivo'].queryset = Dispositivo.objects.filter(cliente=request.user.perfil_usuarios)
        else:
            self.fields['dispositivo'].queryset = Dispositivo.objects.none()

        # ✅ Texto default del select
        self.fields['dispositivo'].empty_label = "Selecciona un dispositivo"

