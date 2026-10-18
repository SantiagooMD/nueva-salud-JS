from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from pacientes.models import Paciente
from pacientes.views import _normalizar
from .forms import ConsultaMedicaForm
from .forms_listado import FiltroConsultasForm
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
        # Ignora tildes y mayúsculas: "maria perez" encuentra a "María José Pérez Gómez".
        palabras = _normalizar(query).split()
        for p in Paciente.objects.filter(activo=True):
            texto = _normalizar(f'{p.numero_documento} {p.nombres} {p.apellidos}')
            if all(palabra in texto for palabra in palabras):
                pacientes.append(p)
        pacientes = pacientes[:20]

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

@login_required
def listado_consultas(request):
    """
    RF-12: Listado de consultas médicas realizadas a un paciente, buscado por:
    - número de documento del paciente (obligatorio)
    - rango de fechas (desde / hasta, opcional)
    Los criterios se validan: una fecha mal escrita o un rango invertido muestra el error
    en el campo en lugar de fallar.
    """
    if not _solo_medico(request.user):
        messages.warning(request, 'Solo el personal médico puede consultar el listado de consultas.')
        return redirect('login')

    hay_criterios = any(
        request.GET.get(campo, '').strip() for campo in ('documento', 'fecha_desde', 'fecha_hasta')
    )
    form = FiltroConsultasForm(request.GET if hay_criterios else None)

    consultas = ConsultaMedica.objects.none()
    paciente = None
    buscado = False

    if hay_criterios and form.is_valid():
        buscado = True
        datos = form.cleaned_data
        # El documento identifica a UN paciente: coincidencia exacta, no parcial.
        paciente = Paciente.objects.filter(numero_documento__iexact=datos['documento']).first()
        if paciente:
            consultas = paciente.consultas.select_related(
                'paciente', 'medico'
            ).prefetch_related('enfermedades', 'medicamentos')
            if datos['fecha_desde']:
                consultas = consultas.filter(fecha_consulta__date__gte=datos['fecha_desde'])
            if datos['fecha_hasta']:
                consultas = consultas.filter(fecha_consulta__date__lte=datos['fecha_hasta'])

    return render(request, 'historia/listado_consultas.html', {
        'form': form,
        'paciente': paciente,
        'consultas': consultas,
        'buscado': buscado,
        'total': consultas.count() if paciente else 0,
    })
