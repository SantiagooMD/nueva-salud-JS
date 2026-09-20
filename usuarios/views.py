from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    """RF-01: Iniciar Sesión"""
    if request.user.is_authenticated:
        return redirect(obtener_url_por_rol(request.user))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(
                    request,
                    f'Bienvenido/a, {user.get_full_name() or user.username}'
                )
                return redirect(obtener_url_por_rol(user))
            else:
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'usuarios/login.html')


def logout_view(request):
    """RF-02: Cerrar Sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


def obtener_url_por_rol(user):
    """Decide a qué página va cada rol después del login"""
    if user.es_administrador:
        return 'dashboard_admin'
    elif user.es_medico:
        return 'dashboard_medico'
    elif user.es_recepcionista:
        return 'dashboard_recepcion'
    return 'login'


@login_required
def dashboard_admin(request):
    if not request.user.es_administrador:
        messages.warning(request, 'No tienes permiso para acceder a esta sección.')
        return redirect(obtener_url_por_rol(request.user))
    return render(request, 'usuarios/dashboard_admin.html')


@login_required
def dashboard_medico(request):
    if not request.user.es_medico:
        messages.warning(request, 'No tienes permiso para acceder a esta sección.')
        return redirect(obtener_url_por_rol(request.user))
    return render(request, 'usuarios/dashboard_medico.html')


@login_required
def dashboard_recepcion(request):
    if not request.user.es_recepcionista:
        messages.warning(request, 'No tienes permiso para acceder a esta sección.')
        return redirect(obtener_url_por_rol(request.user))
    return render(request, 'usuarios/dashboard_recepcion.html')