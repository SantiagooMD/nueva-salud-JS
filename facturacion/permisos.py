from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from usuarios.views import obtener_url_por_rol


def rol_requerido(*roles, mensaje='No tienes permiso para acceder a esta sección.'):
    """Exige sesión iniciada y que el usuario tenga alguno de los roles indicados."""

    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(request, *args, **kwargs):
            if request.user.rol not in roles:
                messages.warning(request, mensaje)
                return redirect(obtener_url_por_rol(request.user))
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador
