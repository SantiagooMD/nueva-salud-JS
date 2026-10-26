from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogos.models import Enfermedad, Medicamento
from pacientes.models import Paciente
from usuarios.models import Usuario

from .models import ConsultaMedica


class ImprimirHistoriaTests(TestCase):
    """RF-13: Imprimir historia clínica completa."""

    def setUp(self):
        self.medico = Usuario.objects.create_user(
            username='medico', password='clave12345', rol=Usuario.Rol.MEDICO,
            first_name='Carlos', last_name='Ramírez', registro_medico='RM-12345',
        )
        self.recep = Usuario.objects.create_user(
            username='recep', password='clave12345', rol=Usuario.Rol.RECEPCIONISTA,
        )
        self.paciente = Paciente.objects.create(
            tipo_documento='CC', numero_documento='1144012345', nombres='María José',
            apellidos='Pérez Gómez', fecha_nacimiento=date(1995, 4, 12), genero='F',
            telefono='3001234567', direccion='Calle 10 # 5-20', email='maria@correo.com',
            tipo_afiliacion='EPS', nombre_eps='EPS Sura',
        )
        gripa = Enfermedad.objects.create(codigo='J06', nombre='Infección respiratoria aguda')
        paracetamol = Medicamento.objects.create(nombre='Paracetamol', presentacion='500 mg')

        ahora = timezone.now()
        self.vieja = ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico, fecha_consulta=ahora - timedelta(days=30),
            motivo='Control antiguo', sintomas='Tos seca y fiebre', tratamiento='Reposo e hidratación',
            observaciones='Volver si empeora',
        )
        self.vieja.enfermedades.add(gripa)
        self.vieja.medicamentos.add(paracetamol)
        self.reciente = ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico, fecha_consulta=ahora,
            motivo='Control reciente',
        )
        self.url = reverse('imprimir_historia', args=[self.paciente.pk])

    def test_contiene_datos_del_paciente_y_de_cada_consulta(self):
        self.client.force_login(self.medico)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        for texto in [
            'María José Pérez Gómez', '1144012345', '12/04/1995', 'Femenino', '3001234567',
            'maria@correo.com', 'Calle 10 # 5-20', 'EPS Sura',
            'Control antiguo', 'Tos seca y fiebre', 'J06 - Infección respiratoria aguda',
            'Reposo e hidratación', 'Volver si empeora', 'Paracetamol (500 mg)',
            'Control reciente', 'RM-12345', 'Carlos Ramírez',
            self.vieja.fecha_consulta.astimezone(timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M'),
        ]:
            self.assertContains(r, texto)

    def test_consultas_en_orden_cronologico(self):
        self.client.force_login(self.medico)
        html = self.client.get(self.url).content.decode()
        self.assertLess(html.index('Control antiguo'), html.index('Control reciente'))

    def test_campos_vacios_se_indican(self):
        self.client.force_login(self.medico)
        r = self.client.get(self.url)
        # La consulta reciente no tiene síntomas, diagnóstico, tratamiento ni observaciones.
        self.assertContains(r, 'Sin diagnóstico registrado.')
        self.assertContains(r, 'Sin información registrada.')
        self.assertContains(r, 'Sin observaciones.')

    def test_paciente_sin_consultas(self):
        ConsultaMedica.objects.all().delete()
        self.client.force_login(self.medico)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'aún no tiene consultas registradas')

    def test_paciente_inactivo_se_puede_imprimir(self):
        Paciente.objects.filter(pk=self.paciente.pk).update(activo=False)
        self.client.force_login(self.medico)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_solo_medicos(self):
        self.client.force_login(self.recep)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.logout()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r.url)

    def test_paciente_inexistente(self):
        self.client.force_login(self.medico)
        self.assertEqual(self.client.get(reverse('imprimir_historia', args=[99999])).status_code, 404)

    def test_boton_imprimir_en_el_historial(self):
        self.client.force_login(self.medico)
        r = self.client.get(reverse('historial_paciente', args=[self.paciente.pk]))
        self.assertContains(r, self.url)


class ImprimirConsultasSeleccionadasTests(ImprimirHistoriaTests):
    """El médico puede imprimir toda la historia o solo las consultas que marque."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.medico)
        self.historial = reverse('historial_paciente', args=[self.paciente.pk])

    def test_historial_ofrece_imprimir_todas_o_seleccionadas(self):
        r = self.client.get(self.historial)
        self.assertContains(r, 'Imprimir todas')
        self.assertContains(r, 'Imprimir seleccionadas')
        self.assertContains(r, f'name="consultas" value="{self.vieja.pk}"')
        self.assertContains(r, f'name="consultas" value="{self.reciente.pk}"')
        self.assertContains(r, 'id="marcar-todas"')

    def test_sin_seleccion_imprime_toda_la_historia(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'Control antiguo')
        self.assertContains(r, 'Control reciente')
        self.assertContains(r, 'historia completa')

    def test_con_seleccion_imprime_solo_las_marcadas(self):
        r = self.client.get(self.url, {'seleccion': '1', 'consultas': [self.reciente.pk]})
        self.assertContains(r, 'Control reciente')
        self.assertNotContains(r, 'Control antiguo')
        self.assertContains(r, '1 de 2 consultas seleccionadas')
        self.assertContains(r, '1144012345')  # los datos del paciente siguen en la hoja

    def test_varias_seleccionadas_salen_en_orden_cronologico(self):
        r = self.client.get(self.url, {'seleccion': '1', 'consultas': [self.reciente.pk, self.vieja.pk]})
        html = r.content.decode()
        self.assertLess(html.index('Control antiguo'), html.index('Control reciente'))

    def test_seleccion_vacia_vuelve_al_historial_con_aviso(self):
        r = self.client.get(self.url, {'seleccion': '1'}, follow=True)
        self.assertRedirects(r, self.historial)
        self.assertContains(r, 'Marca al menos una consulta para imprimir.')

    def test_ids_invalidos_o_de_otro_paciente_se_ignoran(self):
        otro = Paciente.objects.create(
            tipo_documento='CC', numero_documento='999', nombres='Otro', apellidos='Paciente',
            fecha_nacimiento=date(1990, 1, 1), genero='M', tipo_afiliacion='PARTICULAR',
        )
        ajena = ConsultaMedica.objects.create(paciente=otro, medico=self.medico,
                                              fecha_consulta=timezone.now(), motivo='Consulta ajena')
        r = self.client.get(self.url, {'seleccion': '1', 'consultas': ['abc', ajena.pk, self.vieja.pk]})
        self.assertContains(r, 'Control antiguo')
        self.assertNotContains(r, 'Consulta ajena')
        r = self.client.get(self.url, {'seleccion': '1', 'consultas': ['abc', ajena.pk]}, follow=True)
        self.assertRedirects(r, self.historial)

    def test_historial_sin_consultas_no_muestra_botones_de_impresion(self):
        vacio = Paciente.objects.create(
            tipo_documento='CC', numero_documento='555', nombres='Sin', apellidos='Consultas',
            fecha_nacimiento=date(1990, 1, 1), genero='M', tipo_afiliacion='PARTICULAR',
        )
        r = self.client.get(reverse('historial_paciente', args=[vacio.pk]))
        self.assertNotContains(r, 'Imprimir todas')


class ComentariosDePlantillaTests(TestCase):
    def test_ninguna_plantilla_deja_comentarios_de_varias_lineas_con_llaves(self):
        """{# ... #} solo funciona en una línea; si ocupa dos, Django lo imprime como texto."""
        import pathlib
        raiz = pathlib.Path(__file__).resolve().parent.parent
        for ruta in raiz.rglob('*.html'):
            for n, linea in enumerate(ruta.read_text(encoding='utf-8').splitlines(), 1):
                if '{#' in linea:
                    self.assertIn('#}', linea, f'{ruta}:{n} comentario sin cerrar en la misma línea')
