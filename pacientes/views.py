import unicodedata

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PacienteEditForm, PacienteForm
from .models import Paciente


def _normalizar(texto):
    """Minúsculas y sin tildes, para comparar nombres sin importar cómo se escribieron."""
    sin_tildes = unicodedata.normalize('NFD', texto.lower())
    return ''.join(c for c in sin_tildes if unicodedata.category(c) != 'Mn')


@login_required
def registrar_paciente(request):
    """RF-03: Registrar Paciente Nuevo"""
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save()
            messages.success(request, f'Paciente {paciente.nombre_completo} registrado correctamente.')
            return redirect('consultar_paciente')
    else:
        form = PacienteForm()

    return render(request, 'pacientes/registrar_paciente.html', {'form': form})


@login_required
def consultar_paciente(request):
    """RF-04: Consultar Paciente por número de documento o nombre"""
    query = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.filter(activo=True)

    if query:
        pacientes = pacientes.filter(
            Q(numero_documento__icontains=query)
            | Q(nombres__icontains=query)
            | Q(apellidos__icontains=query)
        )

    return render(request, 'pacientes/consultar_paciente.html', {
        'pacientes': pacientes,
        'query': query,
    })


@login_required
def detalle_paciente(request, pk):
    """Ficha de un paciente puntual, enlazada desde el listado de consulta."""
    paciente = get_object_or_404(Paciente, pk=pk)
    return render(request, 'pacientes/detalle_paciente.html', {'paciente': paciente})


@login_required
def actualizar_paciente(request, pk):
    """RF-05: Actualizar Datos del Paciente (solo nombre, teléfono, correo y dirección)"""
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == 'POST':
        form = PacienteEditForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Datos de {paciente.nombre_completo} actualizados correctamente.')
            return redirect('detalle_paciente', pk=paciente.pk)
    else:
        form = PacienteEditForm(instance=paciente)

    return render(request, 'pacientes/actualizar_paciente.html', {'form': form, 'paciente': paciente})


@login_required
def inactivar_paciente(request, pk):
    """RF-06: Inactivar Paciente (pide confirmación antes de ejecutar)"""
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == 'POST':
        paciente.activo = False
        paciente.save(update_fields=['activo'])
        messages.success(request, f'{paciente.nombre_completo} fue inactivado.')
        return redirect('consultar_paciente')

    return render(request, 'pacientes/inactivar_paciente.html', {'paciente': paciente})


@login_required
def buscar_para_consulta(request):
    """
    RF-07: Buscar Paciente para Consulta.
    Búsqueda rápida por número de documento o por nombre/apellido, pensada para el
    momento de iniciar una nueva consulta médica (RF-09, Sprint 2).
    """
    termino = request.GET.get('q', '').strip()
    pacientes = []
    buscado = False

    if termino:
        buscado = True
        # La comparación ignora tildes y mayúsculas: "maria perez" encuentra a
        # "María José Pérez Gómez". Cada palabra escrita debe aparecer en el
        # documento, los nombres o los apellidos.
        palabras = _normalizar(termino).split()
        for p in Paciente.objects.filter(activo=True):
            texto = _normalizar(f'{p.numero_documento} {p.nombres} {p.apellidos}')
            if all(palabra in texto for palabra in palabras):
                pacientes.append(p)

        # Si el término coincide exactamente con un documento, ese paciente va primero.
        pacientes.sort(key=lambda p: p.numero_documento.lower() != termino.lower())
        pacientes = pacientes[:20]

    return render(request, 'pacientes/buscar_para_consulta.html', {
        'termino': termino,
        'pacientes': pacientes,
        'buscado': buscado,
    })


@login_required
@require_POST
def iniciar_consulta(request, pk):
    """
    RF-07: confirma que la consulta del paciente fue iniciada.
    Por ahora solo muestra el mensaje de éxito; el registro de la consulta como tal
    (RF-09) se implementa en el Sprint 2.
    """
    paciente = get_object_or_404(Paciente, pk=pk, activo=True)
    messages.success(
        request,
        f'Consulta iniciada con éxito para {paciente.nombre_completo} '
        f'({paciente.get_tipo_documento_display()} {paciente.numero_documento}).',
    )
    return redirect('buscar_para_consulta')


@login_required
def menu_pacientes(request):
    """Menú principal del módulo de pacientes (recepción)."""
    return render(request, 'pacientes/menu_pacientes.html')
