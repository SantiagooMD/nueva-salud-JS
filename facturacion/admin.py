from django.contrib import admin

from .models import AtencionEPS, Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'consulta', 'valor', 'metodo_pago', 'fecha_registro')
    list_filter = ('metodo_pago',)


@admin.register(AtencionEPS)
class AtencionEPSAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'consulta', 'eps', 'valor_facturable', 'fecha_registro')
    list_filter = ('eps',)
