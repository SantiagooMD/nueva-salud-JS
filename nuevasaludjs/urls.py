from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),          # Panel de administración de Django
    path('', include('usuarios.urls')),       # Nuestras rutas (login, logout, paneles)
    path('pacientes/', include('pacientes.urls')),  # RF-03 a RF-08: gestión de pacientes
]