from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from pacientes.models import Paciente
from .forms import ConsultaMedicaForm
from .models import ConsultaMedica


def _solo_medico(user):
    return user.is_authenticated and user.es_medico


@login_required
def menu_historia(request):
    """Menú del módulo de historia clínica (médico)."""
    if not _solo_medico(request.user):
        messages.warning(request, 'Solo el personal médico puede acceder a historia clínica.')
        return redirect('login')
    return render(request, 'historia/menu_historia.html')


@login_required
def buscar_paciente_historia(request):
    """Buscar paciente para ver historial o registrar consulta."""
    if not _solo_medico(request.user):
        messages.warning(request, 'Solo el personal médico puede acceder a historia clínica.')
        return redirect('login')

    query = request.GET.get('q', '').strip()
    pacientes = []
    if query:
        pacientes = Paciente.objects.filter(activo=True).filter(
            Q(numero_documento__icontains=query)
            | Q(nombres__icontains=query)
            | Q(apellidos__icontains=query)
        )[:20]

    return render(request, 'historia/buscar_paciente.html', {
        'query': query,
        'pacientes': pacientes,
    })


@login_required
def historial_paciente(request, paciente_id):
    """Consultar historial clínico del paciente (lista de consultas)."""
    if not _solo_medico(request.user):
        messages.warning(request, 'Solo el personal médico puede acceder a historia clínica.')
        return redirect('login')

    paciente = get_object_or_404(Paciente, pk=paciente_id, activo=True)
    consultas = paciente.consultas.select_related('medico').prefetch_related(
        'enfermedades', 'medicamentos'
    ).all()

    return render(request, 'historia/historial_paciente.html', {
        'paciente': paciente,
        'consultas': consultas,
    })


@login_required
def registrar_consulta(request, paciente_id):
    """Registrar información de una consulta médica."""
    if not _solo_medico(request.user):
        messages.warning(request, 'Solo el personal médico puede registrar consultas.')
        return redirect('login')

    paciente = get_object_or_404(Paciente, pk=paciente_id, activo=True)

    if request.method == 'POST':
        form = ConsultaMedicaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.paciente = paciente
            consulta.medico = request.user
            consulta.save()
            form.save_m2m()
            messages.success(request, 'Consulta registrada correctamente.')
            return redirect('historial_paciente', paciente_id=paciente.pk)
    else:
        form = ConsultaMedicaForm()

    return render(request, 'historia/form_consulta.html', {
        'form': form,
        'paciente': paciente,
        'titulo': 'Registrar consulta médica',
        'boton': 'Guardar consulta',
    })


@login_required
def detalle_consulta(request, pk):
    """Ver detalle de una consulta."""
    if not _solo_medico(request.user):
        messages.warning(request, 'Solo el personal médico puede ver consultas.')
        return redirect('login')

    consulta = get_object_or_404(
        ConsultaMedica.objects.select_related('paciente', 'medico').prefetch_related(
            'enfermedades', 'medicamentos'
        ),
        pk=pk,
    )
    return render(request, 'historia/detalle_consulta.html', {'consulta': consulta})


@login_required
def actualizar_consulta(request, pk):
    """Actualizar historia clínica (editar una consulta existente)."""
    if not _solo_medico(request.user):
        messages.warning(request, 'Solo el personal médico puede actualizar consultas.')
        return redirect('login')

    consulta = get_object_or_404(ConsultaMedica, pk=pk)
    paciente = consulta.paciente

    if request.method == 'POST':
        form = ConsultaMedicaForm(request.POST, instance=consulta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta actualizada correctamente.')
            return redirect('historial_paciente', paciente_id=paciente.pk)
    else:
        form = ConsultaMedicaForm(instance=consulta)

    return render(request, 'historia/form_consulta.html', {
        'form': form,
        'paciente': paciente,
        'consulta': consulta,
        'titulo': 'Actualizar consulta médica',
        'boton': 'Guardar cambios',
    })
