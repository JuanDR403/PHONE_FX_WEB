from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import RegistroForm
from django.contrib.auth import login

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # No longer logging in the user automatically
            return redirect('logueo:login')  # Redirige a la página de login
    else:
        form = RegistroForm()

    return render(request, 'registro/registro.html', {'form': form})
