from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards por rol (sin usar la palabra "admin" al inicio)
    path('panel/administrador/', views.dashboard_admin, name='dashboard_admin'),
    path('panel/medico/', views.dashboard_medico, name='dashboard_medico'),
    path('panel/recepcion/', views.dashboard_recepcion, name='dashboard_recepcion'),
]