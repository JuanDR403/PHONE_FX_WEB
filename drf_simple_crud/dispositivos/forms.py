from django import forms
from .models import Dispositivo

class DispositivoForm(forms.ModelForm):
    class Meta:

        model = Dispositivo
        fields = ['marca', 'modelo', 'numero_serie']
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
        }
