from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def compress_image(uploaded_image):
    """
    Compresses an image if its dimensions exceed 400x400 pixels.
    Maintains the aspect ratio while resizing.
    """
    img = Image.open(uploaded_image)

    # Check if image needs resizing (if either dimension is > 400px)
    if img.width > 400 or img.height > 400:
        # Calculate new dimensions while maintaining aspect ratio
        if img.width > img.height:
            ratio = 400 / img.width
            new_width = 400
            new_height = int(img.height * ratio)
        else:
            ratio = 400 / img.height
            new_height = 400
            new_width = int(img.width * ratio)

        # Resize the image
        img = img.resize((new_width, new_height), Image.LANCZOS)

        # Save the resized image to a BytesIO object
        output = BytesIO()

        # Determine the format of the original image
        if uploaded_image.name.endswith('.png'):
            img_format = 'PNG'
        elif uploaded_image.name.endswith('.gif'):
            img_format = 'GIF'
        else:
            img_format = 'JPEG'  # Default to JPEG for other formats

        # Save the image with the appropriate format and quality
        if img_format == 'JPEG':
            img.save(output, format=img_format, quality=85)
        else:
            img.save(output, format=img_format)

        output.seek(0)

        # Create a new InMemoryUploadedFile from the resized image
        return InMemoryUploadedFile(
            output,
            'ImageField',
            uploaded_image.name,
            f'image/{img_format.lower()}',
            sys.getsizeof(output),
            None
        )

    # If no resizing is needed, return the original image
    return uploaded_image


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Deja en blanco si no quieres cambiar tu contraseña."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Confirma tu nueva contraseña."
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and not confirm_password:
            self.add_error('confirm_password', 'Por favor, confirma tu nueva contraseña.')

        if confirm_password and not new_password:
            self.add_error('new_password', 'Por favor, ingresa tu nueva contraseña.')

        if new_password and confirm_password:
            if new_password != confirm_password:
                self.add_error('confirm_password', 'Las contraseñas no coinciden.')
            else:
                try:
                    # Validar la contraseña usando las validaciones de Django
                    validate_password(new_password, self.instance)
                except ValidationError as e:
                    self.add_error('new_password', e)

        return cleaned_data


class ProfilePhotoForm(forms.ModelForm):
    """Form for uploading profile photo."""
    class Meta:
        model = Profile
        fields = ['profile_photo']
        widgets = {
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


@login_required
def edit_profile(request):
    """View for editing the logged-in user's profile."""
    # Get or create profile for the user
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Check if this is a photo form submission
        if 'photo_form_submitted' in request.POST:
            photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)

            # Debug: Check if a file was uploaded
            if 'profile_photo' in request.FILES:
                print(f"File uploaded: {request.FILES['profile_photo'].name}")
                print(f"File size: {request.FILES['profile_photo'].size} bytes")
                print(f"File content type: {request.FILES['profile_photo'].content_type}")
            else:
                print("No file uploaded")
                print(f"Request FILES: {request.FILES}")
                print(f"Request POST: {request.POST}")

            if photo_form.is_valid():
                # Don't save the form yet, we need to process the image first
                photo_instance = photo_form.save(commit=False)

                # Check if a new photo was uploaded
                if 'profile_photo' in request.FILES:
                    # Compress the image if needed
                    photo_instance.profile_photo = compress_image(request.FILES['profile_photo'])

                # Now save the photo with the possibly compressed image
                photo_instance.save()

                if profile.profile_photo:
                    print(f"Profile photo saved: {profile.profile_photo.path}")
                    print(f"Profile photo URL: {profile.profile_photo.url}")
                    print(f"Profile photo dimensions: {Image.open(profile.profile_photo.path).size}")
                else:
                    print("No profile photo saved")

                messages.success(request, 'Tu foto de perfil ha sido actualizada correctamente.')
                return redirect('usuarios:edit_profile')
            else:
                messages.error(request, 'Hubo un error al procesar la foto de perfil.')
                form = UserProfileForm(instance=request.user)
                return render(request, 'usuarios/edit_profile.html', {
                    'form': form,
                    'photo_form': photo_form,
                    'profile': profile,
                    'title': 'Editar Perfil'
                })
        else:
            # Regular form submission
            form = UserProfileForm(request.POST, instance=request.user)
            photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)

            # Debug: Check if a file was uploaded
            if 'profile_photo' in request.FILES:
                print(f"File uploaded: {request.FILES['profile_photo'].name}")
            else:
                print("No file uploaded")

            # Validación personalizada antes de is_valid()
            username = request.POST.get('username')
            email = request.POST.get('email')

            if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
                messages.error(request, 'Este nombre de usuario ya está en uso')
                return render(request, 'usuarios/edit_profile.html', {
                    'form': form,
                    'photo_form': photo_form,
                    'profile': profile,
                    'title': 'Editar Perfil'
                })

            if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                messages.error(request, 'Este correo electrónico ya está registrado')
                return render(request, 'usuarios/edit_profile.html', {
                    'form': form,
                    'photo_form': photo_form,
                    'profile': profile,
                    'title': 'Editar Perfil'
                })

            if form.is_valid() and photo_form.is_valid():
                user = form.save(commit=False)

                # Cambiar la contraseña si se proporcionó una nueva
                new_password = form.cleaned_data.get('new_password')
                if new_password:
                    user.set_password(new_password)
                    messages.success(request, 'Tu perfil, contraseña y foto han sido actualizados correctamente.')
                else:
                    messages.success(request, 'Tu perfil y foto han sido actualizados correctamente.')

                user.save()

                # Process and save the profile photo
                if 'profile_photo' in request.FILES:
                    # Don't save the form yet, we need to process the image first
                    photo_instance = photo_form.save(commit=False)

                    # Compress the image if needed
                    photo_instance.profile_photo = compress_image(request.FILES['profile_photo'])

                    # Now save the photo with the possibly compressed image
                    photo_instance.save()
                else:
                    # No new photo uploaded, just save the form
                    photo_form.save()

                if profile.profile_photo:
                    print(f"Profile photo saved: {profile.profile_photo.path}")
                    print(f"Profile photo URL: {profile.profile_photo.url}")
                    print(f"Profile photo dimensions: {Image.open(profile.profile_photo.path).size}")
                else:
                    print("No profile photo saved")

                return redirect('usuarios:edit_profile')
    else:
        form = UserProfileForm(instance=request.user)
        photo_form = ProfilePhotoForm(instance=profile)

    return render(request, 'usuarios/edit_profile.html', {
        'form': form,
        'photo_form': photo_form,
        'profile': profile,
        'title': 'Editar Perfil'
    })
