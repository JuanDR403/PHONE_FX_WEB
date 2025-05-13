from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .forms import EmailAuthenticationForm  # Asegúrate de tener este formulario


@csrf_protect
def login_view(request):
    """
    Vista personalizada para el inicio de sesión con email y contraseña
    """
    if request.user.is_authenticated:
        return redirect('inicio:home')  # Redirige si ya está autenticado

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # Usamos email como username
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.email}!')
                next_url = request.GET.get('next', 'inicio:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Credenciales inválidas. Intente nuevamente.')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = EmailAuthenticationForm()

    return render(request, 'logueo/login.html', {
        'form': form,
        'titulo': 'Iniciar Sesión - PhoneFX'
    })


def logout_view(request):
    """
    Vista para cerrar sesión
    """
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('logueo:login')  # Redirige al login después de logout