from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from pacientes.models import Paciente


@login_required
def imprimir_historia(request, paciente_id):
    """
    RF-13: Imprimir historia clínica completa de un paciente.
    Página lista para imprimir (o guardar como PDF desde el navegador) con los datos del
    paciente y, por cada consulta: fecha, síntomas, diagnóstico, tratamiento y
    observaciones del médico.

    Se permite imprimir también la historia de pacientes inactivos: la historia clínica
    debe poder entregarse aunque el paciente ya no esté activo (Resolución 1995 de 1999).
    """
    if not request.user.es_medico:
        messages.warning(request, 'Solo el personal médico puede imprimir historias clínicas.')
        return redirect('login')

    paciente = get_object_or_404(Paciente, pk=paciente_id)
    # Orden cronológico: de la consulta más antigua a la más reciente.
    consultas = paciente.consultas.select_related('medico').prefetch_related(
        'enfermedades', 'medicamentos',
    ).order_by('fecha_consulta')

    return render(request, 'historia/imprimir_historia.html', {
        'paciente': paciente,
        'consultas': consultas,
        'impreso_por': request.user,
        'fecha_impresion': timezone.localtime(),
    })
