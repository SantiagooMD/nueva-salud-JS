from datetime import date, datetime, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from historia.models import ConsultaMedica
from pacientes.models import Paciente
from usuarios.models import Usuario

from .models import AtencionEPS, Pago
from .templatetags.pesos import formato_pesos


def crear_usuario(username, rol):
    return Usuario.objects.create_user(username=username, password='clave12345', rol=rol)


class BaseFacturacion(TestCase):
    def setUp(self):
        self.recep = crear_usuario('recep', Usuario.Rol.RECEPCIONISTA)
        self.medico = crear_usuario('medico', Usuario.Rol.MEDICO)
        self.admin = crear_usuario('admin1', Usuario.Rol.ADMINISTRADOR)

        self.particular = Paciente.objects.create(
            tipo_documento='CC', numero_documento='1144012345', nombres='María José',
            apellidos='Pérez Gómez', fecha_nacimiento=date(1995, 4, 12), genero='F',
            tipo_afiliacion='PARTICULAR',
        )
        self.eps = Paciente.objects.create(
            tipo_documento='CC', numero_documento='9988776', nombres='Carlos',
            apellidos='Ruiz Díaz', fecha_nacimiento=date(1980, 1, 1), genero='M',
            tipo_afiliacion='EPS', nombre_eps='EPS Sura',
        )
        self.consulta_part = self.nueva_consulta(self.particular)
        self.consulta_eps = self.nueva_consulta(self.eps)

    def nueva_consulta(self, paciente):
        return ConsultaMedica.objects.create(
            paciente=paciente, medico=self.medico, fecha_consulta=timezone.now(), motivo='Control',
        )

    def entrar(self, usuario):
        self.client.force_login(usuario)


class PermisosTests(BaseFacturacion):
    def test_recepcion_accede_y_otros_roles_no(self):
        urls = [
            reverse('menu_facturacion'),
            reverse('consultas_pendientes'),
            reverse('registrar_pago', args=[self.consulta_part.pk]),
            reverse('registrar_atencion_eps', args=[self.consulta_eps.pk]),
            reverse('registros_facturacion'),
        ]
        self.entrar(self.recep)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        for usuario in (self.medico, self.admin):
            self.entrar(usuario)
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_resumen_solo_administrador(self):
        url = reverse('resumen_financiero')
        self.entrar(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)
        for usuario in (self.recep, self.medico):
            self.entrar(usuario)
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_sin_sesion_redirige_al_login(self):
        r = self.client.get(reverse('menu_facturacion'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r.url)


class ConsultasPendientesTests(BaseFacturacion):
    def setUp(self):
        super().setUp()
        self.entrar(self.recep)

    def test_lista_pendientes_con_boton_segun_afiliacion(self):
        r = self.client.get(reverse('consultas_pendientes'))
        self.assertEqual(r.context['total'], 2)
        self.assertContains(r, 'Registrar pago')
        self.assertContains(r, 'Registrar atención EPS')

    def test_busca_por_documento_y_por_nombre_sin_tildes(self):
        url = reverse('consultas_pendientes')
        self.assertEqual(self.client.get(url, {'q': '1144012345'}).context['total'], 1)
        self.assertEqual(self.client.get(url, {'q': 'maria perez'}).context['total'], 1)
        r = self.client.get(url, {'q': 'zzzz'})
        self.assertEqual(r.context['total'], 0)
        self.assertContains(r, 'No hay consultas pendientes para')

    def test_facturadas_dejan_de_aparecer(self):
        Pago.objects.create(consulta=self.consulta_part, valor=50000, metodo_pago='EFECTIVO',
                            registrado_por=self.recep)
        r = self.client.get(reverse('consultas_pendientes'))
        self.assertEqual(r.context['total'], 1)


class ConfidencialidadClinicaTests(BaseFacturacion):
    """Res. 1995/1999: recepción factura, pero no ve el contenido clínico de la consulta."""

    def test_facturacion_no_muestra_motivo_ni_diagnostico(self):
        self.consulta_part.motivo = 'MOTIVO-CONFIDENCIAL-XYZ'
        self.consulta_part.sintomas = 'SINTOMA-CONFIDENCIAL-XYZ'
        self.consulta_part.save()
        self.entrar(self.recep)
        for url in (
            reverse('consultas_pendientes'),
            reverse('registrar_pago', args=[self.consulta_part.pk]),
            reverse('registros_facturacion'),
        ):
            html = self.client.get(url).content.decode()
            self.assertNotIn('CONFIDENCIAL-XYZ', html, url)


class RegistrarPagoTests(BaseFacturacion):
    def setUp(self):
        super().setUp()
        self.entrar(self.recep)
        self.url = reverse('registrar_pago', args=[self.consulta_part.pk])

    def test_pago_valido(self):
        r = self.client.post(self.url, {'valor': '50000', 'metodo_pago': 'EFECTIVO'}, follow=True)
        self.assertRedirects(r, reverse('consultas_pendientes'))
        pago = Pago.objects.get()
        self.assertEqual(pago.valor, Decimal('50000'))
        self.assertEqual(pago.registrado_por, self.recep)
        self.assertEqual(pago.consulta, self.consulta_part)
        self.assertContains(r, 'PAG-')
        self.assertContains(r, '$50.000')

    def test_campos_vacios_muestran_error_por_campo(self):
        r = self.client.post(self.url, {})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ingresa el valor en pesos.')
        self.assertContains(r, 'Selecciona el método de pago.')
        self.assertContains(r, 'is-invalid')
        self.assertFalse(Pago.objects.exists())

    def test_valores_invalidos(self):
        casos = {
            '0': 'El valor debe ser mayor a $0.',
            '-500': 'El valor debe ser mayor a $0.',
            'abc': 'El valor debe ser un número',
            '50000.5': 'sin decimales',
            '9' * 13: 'máximo 12 dígitos',
        }
        for valor, mensaje in casos.items():
            r = self.client.post(self.url, {'valor': valor, 'metodo_pago': 'TARJETA'})
            self.assertContains(r, mensaje, msg_prefix=f'valor={valor!r}')
        self.assertFalse(Pago.objects.exists())

    def test_metodo_de_pago_fuera_de_la_lista(self):
        r = self.client.post(self.url, {'valor': '1000', 'metodo_pago': 'BITCOIN'})
        self.assertContains(r, 'Selecciona un método de pago válido')
        self.assertFalse(Pago.objects.exists())

    def test_no_se_cobra_dos_veces_la_misma_consulta(self):
        datos = {'valor': '50000', 'metodo_pago': 'EFECTIVO'}
        self.client.post(self.url, datos)
        r = self.client.post(self.url, datos, follow=True)
        self.assertEqual(Pago.objects.count(), 1)
        self.assertContains(r, 'ya tiene un pago o una atención registrada')

    def test_paciente_eps_no_se_cobra_directamente(self):
        url = reverse('registrar_pago', args=[self.consulta_eps.pk])
        r = self.client.get(url, follow=True)
        self.assertRedirects(r, reverse('registrar_atencion_eps', args=[self.consulta_eps.pk]))
        self.assertContains(r, 'no se le cobra directamente')
        r = self.client.post(url, {'valor': '50000', 'metodo_pago': 'EFECTIVO'})
        self.assertFalse(Pago.objects.exists())

    def test_consulta_inexistente(self):
        r = self.client.get(reverse('registrar_pago', args=[99999]))
        self.assertEqual(r.status_code, 404)


class RegistrarAtencionEPSTests(BaseFacturacion):
    def setUp(self):
        super().setUp()
        self.entrar(self.recep)
        self.url = reverse('registrar_atencion_eps', args=[self.consulta_eps.pk])

    def test_atencion_valida_guarda_la_eps_del_paciente(self):
        r = self.client.post(self.url, {
            'valor_facturable': '85000', 'numero_autorizacion': 'AUT-2026/123',
        }, follow=True)
        self.assertRedirects(r, reverse('consultas_pendientes'))
        a = AtencionEPS.objects.get()
        self.assertEqual(a.eps, 'EPS Sura')
        self.assertEqual(a.valor_facturable, Decimal('85000'))
        self.assertEqual(a.numero_autorizacion, 'AUT-2026/123')
        self.assertTrue(a.codigo.startswith('ATN-'))
        self.assertContains(r, '$85.000')

    def test_autorizacion_es_opcional(self):
        self.client.post(self.url, {'valor_facturable': '85000'})
        self.assertEqual(AtencionEPS.objects.get().numero_autorizacion, '')

    def test_errores_por_campo(self):
        r = self.client.post(self.url, {'valor_facturable': '', 'numero_autorizacion': 'AB CD!'})
        self.assertContains(r, 'Ingresa el valor en pesos.')
        self.assertContains(r, 'solo puede tener letras, números, guiones y barras')
        self.assertContains(r, 'is-invalid')
        self.assertFalse(AtencionEPS.objects.exists())

    def test_valor_cero_se_rechaza(self):
        r = self.client.post(self.url, {'valor_facturable': '0'})
        self.assertContains(r, 'El valor debe ser mayor a $0.')

    def test_no_se_registra_dos_veces(self):
        self.client.post(self.url, {'valor_facturable': '85000'})
        r = self.client.post(self.url, {'valor_facturable': '85000'}, follow=True)
        self.assertEqual(AtencionEPS.objects.count(), 1)
        self.assertContains(r, 'ya tiene un pago o una atención registrada')

    def test_paciente_particular_redirige_a_pago(self):
        url = reverse('registrar_atencion_eps', args=[self.consulta_part.pk])
        r = self.client.get(url, follow=True)
        self.assertRedirects(r, reverse('registrar_pago', args=[self.consulta_part.pk]))
        self.client.post(url, {'valor_facturable': '85000'})
        self.assertFalse(AtencionEPS.objects.exists())

    def test_consulta_con_pago_no_admite_atencion(self):
        # Caso borde: el paciente pasó de particular a EPS después de pagar.
        Pago.objects.create(consulta=self.consulta_eps, valor=1000, metodo_pago='EFECTIVO',
                            registrado_por=self.recep)
        r = self.client.post(self.url, {'valor_facturable': '85000'}, follow=True)
        self.assertFalse(AtencionEPS.objects.exists())
        self.assertContains(r, 'ya tiene un pago o una atención registrada')


class ResumenFinancieroTests(BaseFacturacion):
    def setUp(self):
        super().setUp()
        self.entrar(self.admin)
        self.url = reverse('resumen_financiero')

    def registrar(self, dias_atras, valor_pago=None, valor_eps=None):
        """Crea pagos/atenciones con fecha de registro `dias_atras` días antes de hoy."""
        fecha = timezone.now() - timedelta(days=dias_atras)
        if valor_pago:
            consulta = self.nueva_consulta(self.particular)
            p = Pago.objects.create(consulta=consulta, valor=valor_pago, metodo_pago='EFECTIVO',
                                    registrado_por=self.recep)
            Pago.objects.filter(pk=p.pk).update(fecha_registro=fecha)
        if valor_eps:
            consulta = self.nueva_consulta(self.eps)
            a = AtencionEPS.objects.create(consulta=consulta, eps='EPS Sura', valor_facturable=valor_eps,
                                           registrado_por=self.recep)
            AtencionEPS.objects.filter(pk=a.pk).update(fecha_registro=fecha)

    def rango(self, desde_dias, hasta_dias):
        hoy = timezone.localdate()
        return {
            'desde': (hoy - timedelta(days=desde_dias)).isoformat(),
            'hasta': (hoy - timedelta(days=hasta_dias)).isoformat(),
        }

    def test_muestra_fecha_tipo_valor_y_total_de_ingresos(self):
        self.registrar(1, valor_pago=50000, valor_eps=80000)
        self.registrar(2, valor_pago=30000)
        r = self.client.get(self.url, self.rango(5, 0))
        self.assertTrue(r.context['consultado'])
        self.assertEqual(r.context['total_ingresos'], Decimal('160000'))
        filas = r.context['filas']
        self.assertEqual(len(filas), 3)
        self.assertEqual({f['tipo'] for f in filas}, {'Particular', 'EPS'})
        self.assertEqual(sum(f['valor'] for f in filas), Decimal('160000'))
        for columna in ('Fecha', 'Tipo de paciente', 'Valor cobrado'):
            self.assertRegex(r.content.decode(), rf'<th[^>]*>\s*{columna}\s*</th>')
        self.assertContains(r, 'Total de ingresos del período')
        self.assertContains(r, '$160.000')

    def test_filas_ordenadas_por_fecha(self):
        self.registrar(1, valor_pago=50000)
        self.registrar(3, valor_eps=80000)
        filas = self.client.get(self.url, self.rango(5, 0)).context['filas']
        self.assertEqual([f['tipo'] for f in filas], ['EPS', 'Particular'])

    def test_el_rango_excluye_lo_que_queda_fuera(self):
        self.registrar(10, valor_pago=99999)
        self.registrar(1, valor_pago=1000)
        r = self.client.get(self.url, self.rango(3, 0))
        self.assertEqual(r.context['total_ingresos'], Decimal('1000'))

    def test_limites_del_rango_son_inclusivos(self):
        self.registrar(0, valor_pago=1000)
        hoy = timezone.localdate().isoformat()
        r = self.client.get(self.url, {'desde': hoy, 'hasta': hoy})
        self.assertEqual(r.context['total_ingresos'], Decimal('1000'))

    def test_rango_sin_movimientos(self):
        r = self.client.get(self.url, self.rango(5, 0))
        self.assertEqual(r.context['total_ingresos'], 0)
        self.assertContains(r, 'No hay pagos ni atenciones registrados en este período.')

    def test_por_defecto_muestra_el_mes_en_curso(self):
        r = self.client.get(self.url)
        hoy = timezone.localdate()
        self.assertTrue(r.context['consultado'])
        self.assertEqual(r.context['desde'], hoy.replace(day=1))
        self.assertEqual(r.context['hasta'], hoy)

    def test_validaciones_del_rango(self):
        r = self.client.get(self.url, {'desde': '2026-10-10', 'hasta': '2026-10-01'})
        self.assertFalse(r.context['consultado'])
        self.assertContains(r, 'La fecha final no puede ser anterior a la fecha de inicio.')
        self.assertContains(r, 'is-invalid')

        r = self.client.get(self.url, {'desde': '', 'hasta': '2026-10-01'})
        self.assertContains(r, 'Selecciona la fecha de inicio del rango.')

        r = self.client.get(self.url, {'desde': 'no-es-fecha', 'hasta': '2026-10-01'})
        self.assertContains(r, 'La fecha de inicio no es válida.')


class FormatoPesosTests(TestCase):
    def test_formato_colombiano(self):
        self.assertEqual(formato_pesos(50000), '$50.000')
        self.assertEqual(formato_pesos(Decimal('1234567')), '$1.234.567')
        self.assertEqual(formato_pesos(0), '$0')
        self.assertEqual(formato_pesos(None), '—')


class RegistrosTests(BaseFacturacion):
    def test_lista_pagos_y_atenciones(self):
        Pago.objects.create(consulta=self.consulta_part, valor=50000, metodo_pago='TARJETA',
                            registrado_por=self.recep)
        AtencionEPS.objects.create(consulta=self.consulta_eps, eps='EPS Sura', valor_facturable=85000,
                                   registrado_por=self.recep)
        self.entrar(self.recep)
        r = self.client.get(reverse('registros_facturacion'))
        self.assertContains(r, '$50.000')
        self.assertContains(r, '$85.000')
        self.assertContains(r, 'Tarjeta')
        self.assertContains(r, 'EPS Sura')


class RegistrosFiltrosTests(BaseFacturacion):
    """El SRS pide que los listados tengan opciones de búsqueda y filtrado."""

    def setUp(self):
        super().setUp()
        self.entrar(self.recep)
        self.url = reverse('registros_facturacion')
        self.pago = Pago.objects.create(consulta=self.consulta_part, valor=50000, metodo_pago='EFECTIVO',
                                        registrado_por=self.recep)
        self.atencion = AtencionEPS.objects.create(consulta=self.consulta_eps, eps='EPS Sura',
                                                   valor_facturable=85000, registrado_por=self.recep)

    def test_sin_filtros_muestra_todo(self):
        r = self.client.get(self.url)
        self.assertEqual(r.context['pagos'], [self.pago])
        self.assertEqual(r.context['atenciones'], [self.atencion])

    def test_filtra_por_documento_o_nombre_sin_tildes(self):
        r = self.client.get(self.url, {'q': '1144012345'})
        self.assertEqual((r.context['pagos'], r.context['atenciones']), ([self.pago], []))
        r = self.client.get(self.url, {'q': 'carlos ruiz'})
        self.assertEqual((r.context['pagos'], r.context['atenciones']), ([], [self.atencion]))
        r = self.client.get(self.url, {'q': 'maria jose'})
        self.assertEqual(r.context['pagos'], [self.pago])

    def test_filtra_por_fechas(self):
        Pago.objects.filter(pk=self.pago.pk).update(fecha_registro=timezone.now() - timedelta(days=10))
        hoy = timezone.localdate()
        r = self.client.get(self.url, {'desde': (hoy - timedelta(days=2)).isoformat(),
                                       'hasta': hoy.isoformat()})
        self.assertEqual((r.context['pagos'], r.context['atenciones']), ([], [self.atencion]))
        self.assertContains(r, 'No hay pagos con esos filtros.')

    def test_fecha_invalida_o_rango_invertido_no_rompen_la_pagina(self):
        r = self.client.get(self.url, {'desde': 'abc'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'La fecha «desde» no es válida.')
        self.assertEqual((r.context['pagos'], r.context['atenciones']), ([], []))
        r = self.client.get(self.url, {'desde': '2026-10-10', 'hasta': '2026-10-01'})
        self.assertContains(r, 'La fecha «hasta» no puede ser anterior a la fecha «desde».')


class ValidacionEnTiempoRealTests(BaseFacturacion):
    """SRS 3.1.1: los formularios incluyen validaciones en tiempo real (static/js/validacion.js)."""

    def test_el_script_existe_y_se_carga_en_las_paginas(self):
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(finders.find('js/validacion.js'))
        self.entrar(self.recep)
        self.assertContains(self.client.get(reverse('menu_facturacion')), 'js/validacion.js')

    def test_formularios_de_facturacion_y_resumen_activan_la_validacion(self):
        self.entrar(self.recep)
        for url in (reverse('registrar_pago', args=[self.consulta_part.pk]),
                    reverse('registrar_atencion_eps', args=[self.consulta_eps.pk]),
                    reverse('registros_facturacion')):
            r = self.client.get(url)
            self.assertContains(r, 'data-validacion="tiempo-real"', msg_prefix=url)
        r = self.client.get(reverse('registrar_pago', args=[self.consulta_part.pk]))
        for atributo in ('required', 'min="1"', 'data-msg-requerido', 'data-msg-min'):
            self.assertContains(r, atributo)
        self.entrar(self.admin)
        r = self.client.get(reverse('resumen_financiero'))
        self.assertContains(r, 'data-validacion="tiempo-real"')
        self.assertContains(r, 'data-min-campo="id_desde"')

    def test_formulario_de_consulta_y_listado_activan_la_validacion(self):
        self.entrar(self.medico)
        r = self.client.get(reverse('registrar_consulta', args=[self.particular.pk]))
        self.assertContains(r, 'data-validacion="tiempo-real"')
        self.assertContains(r, 'data-max-ahora')
        self.assertContains(r, 'minlength="3"')
        r = self.client.get(reverse('listado_consultas'))
        self.assertContains(r, 'data-validacion="tiempo-real"')


class PatronesHtmlTests(TestCase):
    def test_patron_de_autorizacion_escapa_los_caracteres_especiales(self):
        # Chrome compila el atributo pattern en modo /v: "/" y "-" dentro de [] deben ir escapados.
        from .forms import AtencionEPSForm
        patron = AtencionEPSForm().fields['numero_autorizacion'].widget.attrs['pattern']
        self.assertEqual(patron, r'[A-Za-z0-9\/\-]+')
