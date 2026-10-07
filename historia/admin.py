from django.contrib import admin
from .models import ConsultaMedica


@admin.register(ConsultaMedica)
class ConsultaMedicaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico', 'fecha_consulta', 'motivo')
    list_filter = ('fecha_consulta',)
    search_fields = ('paciente__nombres', 'paciente__apellidos', 'paciente__numero_documento', 'motivo')
    filter_horizontal = ('enfermedades', 'medicamentos')
