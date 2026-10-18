from django.urls import path

from . import views

urlpatterns = [
    path('', views.menu_facturacion, name='menu_facturacion'),
    path('pendientes/', views.consultas_pendientes, name='consultas_pendientes'),
    path('consulta/<int:consulta_id>/pago/', views.registrar_pago, name='registrar_pago'),
    path('consulta/<int:consulta_id>/atencion-eps/', views.registrar_atencion_eps, name='registrar_atencion_eps'),
    path('registros/', views.registros_facturacion, name='registros_facturacion'),
    path('resumen/', views.resumen_financiero, name='resumen_financiero'),
]
