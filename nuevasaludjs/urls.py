from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),          # Panel de administración de Django
    path('', include('usuarios.urls')),       # Nuestras rutas (login, logout, paneles)
]