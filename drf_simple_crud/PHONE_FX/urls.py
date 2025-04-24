from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from .views import registro


urlpatterns = [
    path('admin/', admin.site.urls),

    path('registro/',registro, name='registro'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
