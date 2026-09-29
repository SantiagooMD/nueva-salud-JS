from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PacienteEditForm, PacienteForm
from .models import Paciente


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
    Búsqueda rápida por número de documento, pensada para el momento de
    registrar una nueva consulta médica (RF-09, Sprint 2).
    """
    documento = request.GET.get('documento', '').strip()
    paciente = None
    buscado = False

    if documento:
        buscado = True
        paciente = Paciente.objects.filter(
            numero_documento__iexact=documento, activo=True,
        ).first()

    return render(request, 'pacientes/buscar_para_consulta.html', {
        'documento': documento,
        'paciente': paciente,
        'buscado': buscado,
    })


@login_required
def menu_pacientes(request):
    """Menú principal del módulo de pacientes (recepción)."""
    return render(request, 'pacientes/menu_pacientes.html')
