from django.shortcuts import render
from django.contrib.auth.decorators import login_required  # Opcional

@login_required  # Elimina este decorador si quieres acceso público
def home(request):
    context = {
        'titulo': 'Página de Inicio',
        'mensaje': 'Hola, Bienvenido a PhoneFX',
        # Puedes añadir más variables de contexto aquí
    }
    return render(request, 'inicio/home.html', context)
