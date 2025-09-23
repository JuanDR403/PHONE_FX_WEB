from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import RegistroUsuariosForm
from django.contrib.auth import login

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuariosForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Evita guardar inmediatamente

            # Asignar nombre y apellido al modelo User
            user.first_name = request.POST.get('nombre', '')
            user.last_name = request.POST.get('apellido', '')
            user.save()

            # Si también estás creando el modelo Usuarios aquí, lo puedes hacer ahora
            # Usuarios.objects.create(user=user, ...)

            return redirect('logueo:login')  # Redirige a la página de login
    else:
        form = RegistroUsuariosForm()

    return render(request, 'registro/registro.html', {'form': form})
