from django.contrib import admin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('numero_documento', 'nombre_completo', 'tipo_afiliacion', 'activo', 'fecha_registro')
    list_filter = ('tipo_afiliacion', 'activo', 'genero')
    search_fields = ('numero_documento', 'nombres', 'apellidos')
