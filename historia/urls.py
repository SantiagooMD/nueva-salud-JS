from django.urls import path
from . import views, views_impresion

urlpatterns = [
    path('', views.menu_historia, name='menu_historia'),
    path('buscar/', views.buscar_paciente_historia, name='buscar_paciente_historia'),
    path('listado/', views.listado_consultas, name='listado_consultas'),
    path('paciente/<int:paciente_id>/', views.historial_paciente, name='historial_paciente'),
    path('paciente/<int:paciente_id>/nueva/', views.registrar_consulta, name='registrar_consulta'),
    path('paciente/<int:paciente_id>/imprimir/', views_impresion.imprimir_historia, name='imprimir_historia'),
    path('consulta/<int:pk>/', views.detalle_consulta, name='detalle_consulta'),
    path('consulta/<int:pk>/editar/', views.actualizar_consulta, name='actualizar_consulta'),
]