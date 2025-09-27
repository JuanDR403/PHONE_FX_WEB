from django import forms
from productos.models import Producto


class ProductoForm(forms.ModelForm):
    # Campo no mapeado al modelo para permitir carga de archivo
    imagen_archivo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    # Forzar el campo "activo" a ser un select con opciones "Si" y "No"
    ACTIVO_CHOICES = (
        ('Si', 'Si'),
        ('No', 'No'),
    )
    activo = forms.ChoiceField(choices=ACTIVO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}), required=False)

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'categoria', 'activo']  # excluimos 'imagen' para no mostrar URL
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.TextInput(attrs={'class': 'form-control precio-cop','inputmode':'numeric','autocomplete':'off'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }
