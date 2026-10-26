"""Casos límite del cobro automático y de la impresión selectiva."""
from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from historia.models import ConsultaMedica
from pacientes.models import Paciente
from usuarios.models import Usuario

from . import tarifas
from .models import AtencionEPS, Pago


class TarifasTests(TestCase):
    @override_settings(TARIFA_CONSULTA=80000, CUOTA_MODERADORA_EPS=5000)
    def test_valores_normales(self):
        self.assertEqual(tarifas.tarifa_consulta(), Decimal('80000'))
        self.assertEqual(tarifas.cuota_moderadora(), Decimal('5000'))
        self.assertEqual(tarifas.valor_a_facturar_eps(), Decimal('75000'))

    @override_settings(TARIFA_CONSULTA=80000, CUOTA_MODERADORA_EPS=80000)
    def test_cuota_igual_a_la_tarifa_deja_cero_para_la_eps(self):
        self.assertEqual(tarifas.valor_a_facturar_eps(), Decimal('0'))

    @override_settings(TARIFA_CONSULTA=5000, CUOTA_MODERADORA_EPS=20000)
    def test_la_cuota_nunca_supera_la_tarifa(self):
        self.assertEqual(tarifas.cuota_moderadora(), Decimal('5000'))
        self.assertEqual(tarifas.valor_a_facturar_eps(), Decimal('0'))

    @override_settings(TARIFA_CONSULTA=80000, CUOTA_MODERADORA_EPS=0)
    def test_sin_cuota_la_eps_paga_todo(self):
        self.assertEqual(tarifas.valor_a_facturar_eps(), Decimal('80000'))

    def test_cuota_mas_facturable_siempre_suma_la_tarifa(self):
        for tarifa, cuota in ((80000, 5000), (100000, 20100), (150000, 52800), (60000, 0), (3000, 9000)):
            with override_settings(TARIFA_CONSULTA=tarifa, CUOTA_MODERADORA_EPS=cuota):
                self.assertEqual(tarifas.cuota_moderadora() + tarifas.valor_a_facturar_eps(),
                                 tarifas.tarifa_consulta(), (tarifa, cuota))


@override_settings(TARIFA_CONSULTA=80000, CUOTA_MODERADORA_EPS=5000)
class CasosExtremosTests(TestCase):
    def setUp(self):
        self.medico = Usuario.objects.create_user('med', password='x12345678', rol=Usuario.Rol.MEDICO,
                                                  first_name='Carlos', last_name='Ramírez')
        self.recep = Usuario.objects.create_user('rec', password='x12345678', rol=Usuario.Rol.RECEPCIONISTA)
        self.admin = Usuario.objects.create_user('adm', password='x12345678', rol=Usuario.Rol.ADMINISTRADOR)
        self.eps = Paciente.objects.create(
            tipo_documento='CC', numero_documento='1', nombres='Eva', apellidos='Eps',
            fecha_nacimiento=date(1990, 1, 1), genero='F', tipo_afiliacion='EPS', nombre_eps='EPS Sura')
        self.part = Paciente.objects.create(
            tipo_documento='CC', numero_documento='2', nombres='Pablo', apellidos='Part',
            fecha_nacimiento=date(1990, 1, 1), genero='M', tipo_afiliacion='PARTICULAR')
        self.c_eps = ConsultaMedica.objects.create(paciente=self.eps, medico=self.medico,
                                                   fecha_consulta=timezone.now(), motivo='Dolor')
        self.c_part = ConsultaMedica.objects.create(paciente=self.part, medico=self.medico,
                                                    fecha_consulta=timezone.now(), motivo='Gripa')

    # --- cobro
    def test_el_valor_no_se_puede_manipular_por_la_url_ni_el_formulario(self):
        self.client.force_login(self.recep)
        self.client.post(reverse('registrar_pago', args=[self.c_part.pk]),
                         {'metodo_pago': 'EFECTIVO', 'valor': '1', 'registrado_por': self.admin.pk})
        pago = Pago.objects.get()
        self.assertEqual(pago.valor, Decimal('80000'))
        self.assertEqual(pago.registrado_por, self.recep)

    def test_cambiar_la_tarifa_no_modifica_pagos_ya_registrados(self):
        self.client.force_login(self.recep)
        self.client.post(reverse('registrar_pago', args=[self.c_part.pk]), {'metodo_pago': 'EFECTIVO'})
        with override_settings(TARIFA_CONSULTA=200000):
            self.assertEqual(Pago.objects.get().valor, Decimal('80000'))

    def test_get_no_crea_registros(self):
        self.client.force_login(self.recep)
        self.client.get(reverse('registrar_pago', args=[self.c_part.pk]))
        self.client.get(reverse('registrar_atencion_eps', args=[self.c_eps.pk]))
        self.assertFalse(Pago.objects.exists() or AtencionEPS.objects.exists())

    def test_otros_roles_no_pueden_cobrar(self):
        for usuario in (self.medico, self.admin):
            self.client.force_login(usuario)
            self.client.post(reverse('registrar_pago', args=[self.c_part.pk]), {'metodo_pago': 'EFECTIVO'})
            self.client.post(reverse('registrar_atencion_eps', args=[self.c_eps.pk]), {'metodo_pago_cuota': 'EFECTIVO'})
        self.assertFalse(Pago.objects.exists() or AtencionEPS.objects.exists())

    def test_metodo_con_espacios_o_mayusculas_distintas_se_rechaza(self):
        self.client.force_login(self.recep)
        for malo in ('efectivo', ' EFECTIVO', 'EFECTIVO ', '<script>'):
            r = self.client.post(reverse('registrar_pago', args=[self.c_part.pk]), {'metodo_pago': malo})
            self.assertEqual(r.status_code, 200, malo)
        self.assertFalse(Pago.objects.exists())

    def test_observaciones_con_html_se_escapan_en_registros(self):
        self.client.force_login(self.recep)
        self.client.post(reverse('registrar_pago', args=[self.c_part.pk]),
                         {'metodo_pago': 'EFECTIVO', 'observaciones': '<script>alert(1)</script>'})
        r = self.client.get(reverse('registros_facturacion'))
        self.assertNotContains(r, '<script>alert(1)</script>')

    def test_resumen_con_atencion_eps_antigua_sin_cuota(self):
        """Registros creados antes de la cuota moderadora (cuota 0) siguen sumando bien."""
        AtencionEPS.objects.create(consulta=self.c_eps, eps='EPS Sura', valor_facturable=85000,
                                   registrado_por=self.recep)
        self.client.force_login(self.admin)
        hoy = timezone.localdate().isoformat()
        r = self.client.get(reverse('resumen_financiero'), {'desde': hoy, 'hasta': hoy})
        self.assertEqual(r.context['total_cobrado'], Decimal('0'))
        self.assertEqual(r.context['total_eps'], Decimal('85000'))
        self.assertEqual(r.context['total_ingresos'], Decimal('85000'))

    def test_resumen_combinado_cuadra_con_los_registros(self):
        self.client.force_login(self.recep)
        self.client.post(reverse('registrar_pago', args=[self.c_part.pk]), {'metodo_pago': 'TARJETA'})
        self.client.post(reverse('registrar_atencion_eps', args=[self.c_eps.pk]), {'metodo_pago_cuota': 'EFECTIVO'})
        self.client.force_login(self.admin)
        hoy = timezone.localdate().isoformat()
        r = self.client.get(reverse('resumen_financiero'), {'desde': hoy, 'hasta': hoy})
        self.assertEqual(r.context['total_cobrado'], Decimal('85000'))
        self.assertEqual(r.context['total_eps'], Decimal('75000'))
        self.assertEqual(r.context['total_ingresos'], Decimal('160000'))
        self.assertEqual(len(r.context['filas']), 2)

    # --- impresión selectiva
    def test_id_enorme_en_la_seleccion_no_rompe_la_pagina(self):
        self.client.force_login(self.medico)
        url = reverse('imprimir_historia', args=[self.eps.pk])
        for ids in (['9' * 40], ['-1'], ['1.5'], [''], ['0'], ['²'], ['٣'], ['１２']):
            r = self.client.get(url, {'seleccion': '1', 'consultas': ids})
            self.assertIn(r.status_code, (200, 302), ids)
        r = self.client.get(url, {'seleccion': '1', 'consultas': ['9' * 40, self.c_eps.pk]})
        self.assertContains(r, 'Dolor')

    def test_consulta_repetida_en_la_seleccion_sale_una_sola_vez(self):
        self.client.force_login(self.medico)
        r = self.client.get(reverse('imprimir_historia', args=[self.eps.pk]),
                            {'seleccion': '1', 'consultas': [self.c_eps.pk] * 3})
        self.assertContains(r, '1 de 1 consultas seleccionadas')
        self.assertEqual(r.content.decode().count('Motivo de consulta'), 1)

    def test_texto_html_en_la_consulta_se_escapa_al_imprimir(self):
        self.c_eps.motivo = '<img src=x onerror=alert(1)>'
        self.c_eps.save()
        self.client.force_login(self.medico)
        for url in (reverse('imprimir_historia', args=[self.eps.pk]),
                    reverse('historial_paciente', args=[self.eps.pk])):
            r = self.client.get(url)
            self.assertNotContains(r, '<img src=x onerror=alert(1)>')

    def test_recepcion_y_admin_no_imprimen_ni_con_seleccion(self):
        for usuario in (self.recep, self.admin):
            self.client.force_login(usuario)
            r = self.client.get(reverse('imprimir_historia', args=[self.eps.pk]),
                                {'seleccion': '1', 'consultas': [self.c_eps.pk]})
            self.assertEqual(r.status_code, 302)
            self.assertNotIn('imprimir', r.url)

    def test_seleccion_del_paciente_a_no_muestra_consultas_del_paciente_b(self):
        self.client.force_login(self.medico)
        r = self.client.get(reverse('imprimir_historia', args=[self.eps.pk]),
                            {'seleccion': '1', 'consultas': [self.c_part.pk]}, follow=True)
        self.assertNotContains(r, 'Gripa')
