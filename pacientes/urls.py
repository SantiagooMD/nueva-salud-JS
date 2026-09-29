from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu_pacientes, name='menu_pacientes'),
    path('registrar/', views.registrar_paciente, name='registrar_paciente'),
    path('consultar/', views.consultar_paciente, name='consultar_paciente'),
    path('buscar-consulta/', views.buscar_para_consulta, name='buscar_para_consulta'),
    path('<int:pk>/iniciar-consulta/', views.iniciar_consulta, name='iniciar_consulta'),
    path('<int:pk>/', views.detalle_paciente, name='detalle_paciente'),
    path('<int:pk>/actualizar/', views.actualizar_paciente, name='actualizar_paciente'),
    path('<int:pk>/inactivar/', views.inactivar_paciente, name='inactivar_paciente'),
]