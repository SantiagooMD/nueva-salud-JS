from django.contrib import admin
from .models import Enfermedad, Medicamento


@admin.register(Enfermedad)
class EnfermedadAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre')


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'presentacion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


