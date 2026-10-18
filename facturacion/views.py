from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from historia.models import ConsultaMedica
from pacientes.models import Paciente
from pacientes.views import _normalizar
from usuarios.models import Usuario

from .forms import AtencionEPSForm, FiltroRegistrosForm, PagoForm, RangoFechasForm
from .models import AtencionEPS, Pago
from .permisos import rol_requerido
from .templatetags.pesos import formato_pesos as _formato_pesos

solo_recepcion = rol_requerido(
    Usuario.Rol.RECEPCIONISTA,
    mensaje='Solo el personal de recepción puede acceder a facturación.',
)
solo_administrador = rol_requerido(
    Usuario.Rol.ADMINISTRADOR,
    mensaje='Solo el administrador puede consultar el resumen financiero.',
)

LIMITE_FILAS = 50


def _ya_facturada(consulta):
    return Pago.objects.filter(consulta=consulta).exists() or \
        AtencionEPS.objects.filter(consulta=consulta).exists()


@solo_recepcion
def menu_facturacion(request):
    """Menú del módulo de facturación (recepción)."""
    pendientes = ConsultaMedica.objects.filter(pago__isnull=True, atencion_eps__isnull=True).count()
    return render(request, 'facturacion/menu_facturacion.html', {'pendientes': pendientes})


@solo_recepcion
def consultas_pendientes(request):
    """
    Consultas médicas que todavía no tienen pago ni atención EPS registrada.
    Se puede buscar por número de documento o por nombre del paciente.
    """
    termino = request.GET.get('q', '').strip()
    consultas = ConsultaMedica.objects.filter(
        pago__isnull=True, atencion_eps__isnull=True,
    ).select_related('paciente', 'medico')

    if termino:
        palabras = _normalizar(termino).split()
        consultas = [
            c for c in consultas
            if all(
                palabra in _normalizar(
                    f'{c.paciente.numero_documento} {c.paciente.nombres} {c.paciente.apellidos}'
                )
                for palabra in palabras
            )
        ]
    else:
        consultas = list(consultas)

    total = len(consultas)
    return render(request, 'facturacion/consultas_pendientes.html', {
        'consultas': consultas[:LIMITE_FILAS],
        'total': total,
        'limite': LIMITE_FILAS,
        'termino': termino,
    })


@solo_recepcion
def registrar_pago(request, consulta_id):
    """RF-14: Registrar pago de una consulta realizada por un paciente particular."""
    consulta = get_object_or_404(
        ConsultaMedica.objects.select_related('paciente', 'medico'), pk=consulta_id,
    )
    paciente = consulta.paciente

    if _ya_facturada(consulta):
        messages.warning(request, 'Esta consulta ya tiene un pago o una atención registrada.')
        return redirect('consultas_pendientes')

    if paciente.tipo_afiliacion == Paciente.TipoAfiliacion.EPS:
        messages.warning(
            request,
            f'{paciente.nombre_completo} es paciente EPS y no se le cobra directamente. '
            'Registra la atención EPS.',
        )
        return redirect('registrar_atencion_eps', consulta_id=consulta.pk)

    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.consulta = consulta
            pago.registrado_por = request.user
            try:
                with transaction.atomic():
                    pago.save()
            except IntegrityError:
                messages.warning(request, 'Esta consulta ya tiene un pago o una atención registrada.')
                return redirect('consultas_pendientes')
            messages.success(
                request,
                f'Pago {pago.numero} de {_formato_pesos(pago.valor)} registrado para '
                f'{paciente.nombre_completo}.',
            )
            return redirect('consultas_pendientes')
    else:
        form = PagoForm()

    return render(request, 'facturacion/form_pago.html', {
        'form': form, 'consulta': consulta, 'paciente': paciente,
    })


@solo_recepcion
def registrar_atencion_eps(request, consulta_id):
    """RF-15: Registrar la atención médica de un paciente remitido por una EPS."""
    consulta = get_object_or_404(
        ConsultaMedica.objects.select_related('paciente', 'medico'), pk=consulta_id,
    )
    paciente = consulta.paciente

    if _ya_facturada(consulta):
        messages.warning(request, 'Esta consulta ya tiene un pago o una atención registrada.')
        return redirect('consultas_pendientes')

    if paciente.tipo_afiliacion != Paciente.TipoAfiliacion.EPS:
        messages.warning(
            request,
            f'{paciente.nombre_completo} es paciente particular. Registra el pago de la consulta.',
        )
        return redirect('registrar_pago', consulta_id=consulta.pk)

    if request.method == 'POST':
        form = AtencionEPSForm(request.POST)
        if form.is_valid():
            atencion = form.save(commit=False)
            atencion.consulta = consulta
            atencion.eps = paciente.nombre_eps
            atencion.registrado_por = request.user
            try:
                with transaction.atomic():
                    atencion.save()
            except IntegrityError:
                messages.warning(request, 'Esta consulta ya tiene un pago o una atención registrada.')
                return redirect('consultas_pendientes')
            messages.success(
                request,
                f'Atención {atencion.codigo} registrada para {paciente.nombre_completo} '
                f'({atencion.eps}). Valor a facturar a la EPS: {_formato_pesos(atencion.valor_facturable)}.',
            )
            return redirect('consultas_pendientes')
    else:
        form = AtencionEPSForm()

    return render(request, 'facturacion/form_atencion_eps.html', {
        'form': form, 'consulta': consulta, 'paciente': paciente,
    })


def _coincide_paciente(paciente, palabras):
    texto = _normalizar(f'{paciente.numero_documento} {paciente.nombres} {paciente.apellidos}')
    return all(palabra in texto for palabra in palabras)


@solo_recepcion
def registros_facturacion(request):
    """
    Pagos y atenciones EPS ya registrados, para verificar lo que se ha capturado.
    Se puede filtrar por paciente (documento o nombre) y por rango de fechas.
    """
    hay_filtros = any(request.GET.get(k, '').strip() for k in ('q', 'desde', 'hasta'))
    form = FiltroRegistrosForm(request.GET if hay_filtros else None)
    valido = form.is_valid() if hay_filtros else True
    filtros = form.cleaned_data if hay_filtros and valido else {}

    pagos = Pago.objects.select_related('consulta__paciente')
    atenciones = AtencionEPS.objects.select_related('consulta__paciente')
    if filtros.get('desde'):
        pagos = pagos.filter(fecha_registro__date__gte=filtros['desde'])
        atenciones = atenciones.filter(fecha_registro__date__gte=filtros['desde'])
    if filtros.get('hasta'):
        pagos = pagos.filter(fecha_registro__date__lte=filtros['hasta'])
        atenciones = atenciones.filter(fecha_registro__date__lte=filtros['hasta'])

    if not valido:
        pagos, atenciones = Pago.objects.none(), AtencionEPS.objects.none()

    pagos, atenciones = list(pagos), list(atenciones)
    if filtros.get('q'):
        palabras = _normalizar(filtros['q']).split()
        pagos = [p for p in pagos if _coincide_paciente(p.consulta.paciente, palabras)]
        atenciones = [a for a in atenciones if _coincide_paciente(a.consulta.paciente, palabras)]

    return render(request, 'facturacion/registros.html', {
        'form': form,
        'filtrado': bool(filtros),
        'pagos': pagos[:LIMITE_FILAS],
        'atenciones': atenciones[:LIMITE_FILAS],
        'total_pagos': len(pagos),
        'total_atenciones': len(atenciones),
        'limite': LIMITE_FILAS,
    })


@solo_administrador
def resumen_financiero(request):
    """
    RF-16: Resumen financiero del consultorio en un rango de fechas.
    Muestra fecha, tipo de paciente (EPS o particular), valor y el total de
    ingresos del período. Por defecto muestra el mes en curso.
    """
    hoy = timezone.localdate()
    if request.GET.get('desde') or request.GET.get('hasta'):
        form = RangoFechasForm(request.GET)
    else:
        form = RangoFechasForm({'desde': hoy.replace(day=1).isoformat(), 'hasta': hoy.isoformat()})

    contexto = {'form': form, 'consultado': False}

    if form.is_valid():
        desde, hasta = form.cleaned_data['desde'], form.cleaned_data['hasta']
        pagos = Pago.objects.filter(
            fecha_registro__date__gte=desde, fecha_registro__date__lte=hasta,
        )
        atenciones = AtencionEPS.objects.filter(
            fecha_registro__date__gte=desde, fecha_registro__date__lte=hasta,
        )

        # Una fila por cada pago (paciente particular) o atención (paciente EPS) del período.
        filas = [
            {'fecha': p.fecha_registro, 'tipo': 'Particular', 'valor': p.valor} for p in pagos
        ] + [
            {'fecha': a.fecha_registro, 'tipo': 'EPS', 'valor': a.valor_facturable} for a in atenciones
        ]
        filas.sort(key=lambda f: f['fecha'])
        total_ingresos = sum((f['valor'] for f in filas), 0)

        contexto.update({
            'consultado': True,
            'desde': desde,
            'hasta': hasta,
            'filas': filas,
            'total_ingresos': total_ingresos,
        })

    return render(request, 'facturacion/resumen_financiero.html', contexto)
