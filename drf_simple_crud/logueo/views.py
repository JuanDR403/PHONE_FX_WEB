from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import EmailOrUsernameAuthenticationForm


def login_view(request):
    # Si el usuario ya está autenticado, redirige al home
    if request.user.is_authenticated:
        return redirect('inicio:home')

    if request.method == 'POST':
        form = EmailOrUsernameAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                login(request, user)
                # Usar el nombre de usuario si está disponible, de lo contrario usar el email
                display_name = user.username if user.username else user.email
                messages.success(request, f'¡Bienvenido {display_name}!')

                # Redirige a 'next' si está presente y no está vacío, de lo contrario al home
                next_url = request.POST.get('next', request.GET.get('next', ''))
                if next_url and next_url.strip():
                    return redirect(next_url)
                else:
                    return redirect('inicio:home')

            except Exception as e:
                messages.error(request, f"Error al iniciar sesión: {str(e)}")
        else:
            # Pasa los errores del formulario a los mensajes
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = EmailOrUsernameAuthenticationForm()

    return render(request, 'logueo/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


def logout_view(request):
    logout(request)
    messages.success(request, '¡Has cerrado sesión correctamente!')
    return redirect('logueo:login')
