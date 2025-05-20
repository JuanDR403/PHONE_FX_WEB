from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


@login_required
def edit_profile(request):
    """View for editing the logged-in user's profile."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)

        # Validación personalizada antes de is_valid()
        username = request.POST.get('username')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
            messages.error(request, 'Este nombre de usuario ya está en uso')
            return render(request, 'usuarios/edit_profile.html', {
                'form': form,
                'title': 'Editar Perfil'
            })

        if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'Este correo electrónico ya está registrado')
            return render(request, 'usuarios/edit_profile.html', {
                'form': form,
                'title': 'Editar Perfil'
            })

        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('usuarios:edit_profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'usuarios/edit_profile.html', {
        'form': form,
        'title': 'Editar Perfil'
    })