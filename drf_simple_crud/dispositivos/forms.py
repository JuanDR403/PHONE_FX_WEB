# dispositivos/forms.py
from django import forms
from .models import Dispositivo

class DispositivoForm(forms.ModelForm):
    # Opciones de marcas
    MARCA_CHOICES = [
        ('', 'Selecciona una marca'),
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

    marca = forms.ChoiceField(
        choices=MARCA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_marca'}),
        label='Marca',
        required=True
    )

    # ✅ CAMBIO IMPORTANTE: Cambiar a CharField en lugar de ChoiceField
    modelo = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Selecciona un modelo',
            'id': 'id_modelo'
        }),
        label='Modelo',
        required=True
    )

    class Meta:
        model = Dispositivo
        fields = ['marca', 'modelo', 'numero_serie']
        widgets = {
            'numero_serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de serie (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero_serie'].required = False