from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from pacientes.models import Paciente


@login_required
def imprimir_historia(request, paciente_id):
    """
    RF-13: Imprimir historia clínica de un paciente.
    Sin fechas imprime toda la historia. Con desde y/o hasta imprime solo
    las consultas de ese rango.
    """
    if not request.user.es_medico:
        messages.warning(request, 'Solo el personal médico puede imprimir historias clínicas.')
        return redirect('login')

    paciente = get_object_or_404(Paciente, pk=paciente_id)
    todas = paciente.consultas.all()
    total_consultas = todas.count()

    desde_txt = (request.GET.get('desde') or '').strip()
    hasta_txt = (request.GET.get('hasta') or '').strip()
    parcial = bool(desde_txt or hasta_txt)

    if parcial:
        try:
            if desde_txt:
                desde = timezone.datetime.strptime(desde_txt, '%Y-%m-%d').date()
                todas = todas.filter(fecha_consulta__date__gte=desde)
            if hasta_txt:
                hasta = timezone.datetime.strptime(hasta_txt, '%Y-%m-%d').date()
                todas = todas.filter(fecha_consulta__date__lte=hasta)
            if desde_txt and hasta_txt and desde > hasta:
                messages.warning(request, 'La fecha desde no puede ser posterior a la fecha hasta.')
                return redirect('historial_paciente', paciente_id=paciente.pk)
        except ValueError:
            messages.warning(request, 'Las fechas del rango no son válidas.')
            return redirect('historial_paciente', paciente_id=paciente.pk)

        if not todas.exists():
            messages.warning(request, 'No hay consultas en ese rango de fechas.')
            return redirect('historial_paciente', paciente_id=paciente.pk)

    consultas = todas.select_related('medico').prefetch_related(
        'enfermedades', 'medicamentos',
    ).order_by('fecha_consulta')

    return render(request, 'historia/imprimir_historia.html', {
        'paciente': paciente,
        'consultas': consultas,
        'parcial': parcial,
        'total_consultas': total_consultas,
        'impreso_por': request.user,
        'fecha_impresion': timezone.localtime(),
    })