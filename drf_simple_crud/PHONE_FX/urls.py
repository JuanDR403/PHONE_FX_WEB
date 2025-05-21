from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('registro/', include('registro.urls')),
    path('home/', include('inicio.urls')),
    path('login/', include('logueo.urls')),
    path('password-reset/', include('reset_password.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('', RedirectView.as_view(url='/login/'), name='root-redirect'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
