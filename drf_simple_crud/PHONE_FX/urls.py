from django.contrib import admin
from django.urls import path
from .views import registro

urlpatterns = [
    path('admin/', admin.site.urls),

    path('registro/',registro, name='registro'),
]
