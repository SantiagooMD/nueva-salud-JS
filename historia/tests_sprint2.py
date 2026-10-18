import re
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogos.models import Enfermedad, Medicamento
from pacientes.models import Paciente
from usuarios.models import Usuario

from .models import ConsultaMedica


def ahora_local():
    return timezone.localtime().strftime('%Y-%m-%dT%H:%M')


class BaseHistoria(TestCase):
    def setUp(self):
        self.medico = Usuario.objects.create_user(
            username='medico', password='clave12345', rol=Usuario.Rol.MEDICO,
            first_name='Carlos', last_name='Ramírez',
        )
        self.recep = Usuario.objects.create_user(
            username='recep', password='clave12345', rol=Usuario.Rol.RECEPCIONISTA,
        )
        self.paciente = Paciente.objects.create(
            tipo_documento='CC', numero_documento='1144012345', nombres='María José',
            apellidos='Pérez Gómez', fecha_nacimiento=date(1995, 4, 12), genero='F',
        )
        self.dx = Enfermedad.objects.create(codigo='ZZ1', nombre='Diagnóstico de prueba')
        self.med = Medicamento.objects.create(nombre='Medicamento de prueba', presentacion='10 mg')
        self.client.force_login(self.medico)

    def datos(self, **cambios):
        datos = {
            'fecha_consulta': ahora_local(),
            'motivo': 'Dolor de garganta',
            'sintomas': 'Dolor al tragar',
            'enfermedades': [self.dx.pk],
            'medicamentos': [self.med.pk],
            'tratamiento': 'Reposo',
            'observaciones': '',
        }
        datos.update(cambios)
        return datos


class RegistrarConsultaTests(BaseHistoria):
    """RF-09: Registrar consulta médica."""

    def setUp(self):
        super().setUp()
        self.url = reverse('registrar_consulta', args=[self.paciente.pk])

    def test_registro_valido(self):
        r = self.client.post(self.url, self.datos(), follow=True)
        self.assertRedirects(r, reverse('historial_paciente', args=[self.paciente.pk]))
        c = ConsultaMedica.objects.get()
        self.assertEqual(c.medico, self.medico)
        self.assertEqual(c.paciente, self.paciente)
        self.assertEqual(list(c.enfermedades.all()), [self.dx])
        self.assertEqual(list(c.medicamentos.all()), [self.med])
        self.assertContains(r, 'Consulta registrada correctamente.')

    def test_campos_vacios_muestran_error_por_campo_en_rojo(self):
        r = self.client.post(self.url, {})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ingresa la fecha y hora de la consulta.')
        self.assertContains(r, 'Ingresa el motivo de la consulta.')
        self.assertContains(r, 'is-invalid')
        self.assertFalse(ConsultaMedica.objects.exists())

    def test_fecha_futura_se_rechaza(self):
        futura = (timezone.localtime() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        r = self.client.post(self.url, self.datos(fecha_consulta=futura))
        self.assertContains(r, 'no puede ser posterior a la fecha y hora actual')
        self.assertFalse(ConsultaMedica.objects.exists())

    def test_fecha_con_formato_invalido(self):
        r = self.client.post(self.url, self.datos(fecha_consulta='ayer'))
        self.assertContains(r, 'La fecha de la consulta no es válida')

    def test_motivo_muy_corto_o_solo_espacios(self):
        for motivo in ('ab', '   '):
            r = self.client.post(self.url, self.datos(motivo=motivo))
            self.assertEqual(r.status_code, 200, motivo)
        self.assertFalse(ConsultaMedica.objects.exists())

    def test_catalogo_inactivo_no_se_puede_seleccionar(self):
        Enfermedad.objects.filter(pk=self.dx.pk).update(activo=False)
        r = self.client.post(self.url, self.datos())
        self.assertEqual(r.status_code, 200)
        self.assertIn('enfermedades', r.context['form'].errors)

    def test_sin_diagnostico_ni_medicamento_es_valido(self):
        r = self.client.post(self.url, self.datos(enfermedades=[], medicamentos=[]))
        self.assertEqual(r.status_code, 302)

    def test_solo_medicos(self):
        self.client.force_login(self.recep)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, self.datos()).status_code, 302)
        self.assertFalse(ConsultaMedica.objects.exists())

    def test_paciente_inactivo_no_admite_consulta(self):
        Paciente.objects.filter(pk=self.paciente.pk).update(activo=False)
        self.assertEqual(self.client.get(self.url).status_code, 404)


class ActualizarConsultaTests(BaseHistoria):
    """RF-10: Actualizar historia clínica."""

    def setUp(self):
        super().setUp()
        self.consulta = ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico,
            fecha_consulta=timezone.now() - timedelta(days=1), motivo='Control',
        )
        self.url = reverse('actualizar_consulta', args=[self.consulta.pk])

    def test_el_formulario_muestra_los_datos_actuales_en_hora_local(self):
        r = self.client.get(self.url)
        esperado = timezone.localtime(self.consulta.fecha_consulta).strftime('%Y-%m-%dT%H:%M')
        self.assertContains(r, f'value="{esperado}"')
        self.assertContains(r, 'Control')

    def test_actualizacion_valida(self):
        r = self.client.post(self.url, self.datos(motivo='Control actualizado'), follow=True)
        self.assertRedirects(r, reverse('historial_paciente', args=[self.paciente.pk]))
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.motivo, 'Control actualizado')
        self.assertEqual(list(self.consulta.enfermedades.all()), [self.dx])
        self.assertContains(r, 'Consulta actualizada correctamente.')

    def test_actualizar_no_cambia_paciente_ni_medico_original(self):
        otro = Usuario.objects.create_user(username='medico2', password='x12345678', rol=Usuario.Rol.MEDICO)
        self.client.force_login(otro)
        self.client.post(self.url, self.datos(motivo='Cambiado por otro médico'))
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.medico, self.medico)
        self.assertEqual(self.consulta.paciente, self.paciente)

    def test_actualizacion_invalida_conserva_la_consulta(self):
        r = self.client.post(self.url, self.datos(motivo=''))
        self.assertContains(r, 'Ingresa el motivo de la consulta.')
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.motivo, 'Control')

    def test_solo_medicos(self):
        self.client.force_login(self.recep)
        self.assertEqual(self.client.post(self.url, self.datos(motivo='Hack')).status_code, 302)
        self.consulta.refresh_from_db()
        self.assertEqual(self.consulta.motivo, 'Control')


class HistorialYDetalleTests(BaseHistoria):
    """RF-11: Consultar historial clínico."""

    def test_historial_lista_las_consultas_del_paciente_mas_recientes_primero(self):
        ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico,
            fecha_consulta=timezone.now() - timedelta(days=5), motivo='Consulta vieja',
        )
        ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico,
            fecha_consulta=timezone.now(), motivo='Consulta nueva',
        )
        html = self.client.get(reverse('historial_paciente', args=[self.paciente.pk])).content.decode()
        self.assertLess(html.index('Consulta nueva'), html.index('Consulta vieja'))

    def test_historial_no_mezcla_pacientes(self):
        otro = Paciente.objects.create(
            tipo_documento='CC', numero_documento='555666', nombres='Otro', apellidos='Paciente',
            fecha_nacimiento=date(1990, 1, 1), genero='M',
        )
        ConsultaMedica.objects.create(
            paciente=otro, medico=self.medico, fecha_consulta=timezone.now(), motivo='Del otro paciente',
        )
        r = self.client.get(reverse('historial_paciente', args=[self.paciente.pk]))
        self.assertNotContains(r, 'Del otro paciente')
        self.assertContains(r, 'aún no tiene consultas registradas')

    def test_detalle_muestra_toda_la_informacion(self):
        c = ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico, fecha_consulta=timezone.now(),
            motivo='Fiebre', sintomas='Fiebre alta', tratamiento='Reposo', observaciones='Volver en 3 días',
        )
        c.enfermedades.add(self.dx)
        c.medicamentos.add(self.med)
        r = self.client.get(reverse('detalle_consulta', args=[c.pk]))
        for texto in ('Fiebre alta', 'Reposo', 'Volver en 3 días', 'Diagnóstico de prueba', 'Medicamento de prueba'):
            self.assertContains(r, texto)

    def test_solo_medicos(self):
        self.client.force_login(self.recep)
        self.assertEqual(self.client.get(reverse('historial_paciente', args=[self.paciente.pk])).status_code, 302)


class BuscarPacienteHistoriaTests(BaseHistoria):
    def buscar(self, q):
        return self.client.get(reverse('buscar_paciente_historia'), {'q': q})

    def test_por_documento_y_por_nombre(self):
        self.assertEqual(list(self.buscar('1144012345').context['pacientes']), [self.paciente])
        self.assertEqual(list(self.buscar('Pérez').context['pacientes']), [self.paciente])

    def test_ignora_tildes_y_mayusculas(self):
        # Igual que la búsqueda de recepción (RF-07): "maria perez" encuentra a "María José Pérez Gómez".
        self.assertEqual(list(self.buscar('maria perez').context['pacientes']), [self.paciente])
        self.assertEqual(list(self.buscar('JOSE GOMEZ').context['pacientes']), [self.paciente])

    def test_no_muestra_inactivos(self):
        Paciente.objects.filter(pk=self.paciente.pk).update(activo=False)
        self.assertEqual(list(self.buscar('maria').context['pacientes']), [])


class ListadoConsultasTests(BaseHistoria):
    """RF-12: Listado de consultas por documento y rango de fechas."""

    def setUp(self):
        super().setUp()
        self.url = reverse('listado_consultas')
        self.otro = Paciente.objects.create(
            tipo_documento='CC', numero_documento='9988776', nombres='Carlos', apellidos='Ruiz',
            fecha_nacimiento=date(1980, 1, 1), genero='M',
        )
        hoy = timezone.now()
        self.c_vieja = ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico, fecha_consulta=hoy - timedelta(days=20), motivo='Vieja',
        )
        self.c_reciente = ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico, fecha_consulta=hoy - timedelta(days=1), motivo='Reciente',
        )
        self.c_otro = ConsultaMedica.objects.create(
            paciente=self.otro, medico=self.medico, fecha_consulta=hoy - timedelta(days=1), motivo='Del otro',
        )

    def dia(self, dias_atras):
        return (timezone.localdate() - timedelta(days=dias_atras)).isoformat()

    def test_sin_criterios_pide_ingresarlos(self):
        r = self.client.get(self.url)
        self.assertFalse(r.context['buscado'])
        self.assertContains(r, 'Ingresa el documento del paciente')

    def test_por_documento(self):
        r = self.client.get(self.url, {'documento': '1144012345'})
        self.assertEqual(set(r.context['consultas']), {self.c_vieja, self.c_reciente})

    def test_sin_documento_no_busca_aunque_haya_fechas(self):
        # El listado es de UN paciente: el documento es obligatorio.
        r = self.client.get(self.url, {'fecha_desde': self.dia(3), 'fecha_hasta': self.dia(0)})
        self.assertFalse(r.context['buscado'])
        self.assertContains(r, 'Ingresa el número de documento del paciente.')
        self.assertEqual(r.context['total'], 0)

    def test_documento_y_rango_combinados(self):
        r = self.client.get(self.url, {
            'documento': '1144012345', 'fecha_desde': self.dia(3), 'fecha_hasta': self.dia(0),
        })
        self.assertEqual(list(r.context['consultas']), [self.c_reciente])
        self.assertEqual(r.context['paciente'], self.paciente)

    def test_solo_muestra_consultas_de_ese_paciente(self):
        r = self.client.get(self.url, {'documento': '1144012345', 'fecha_desde': self.dia(30), 'fecha_hasta': self.dia(0)})
        self.assertNotIn(self.c_otro, r.context['consultas'])

    def test_el_documento_se_busca_exacto_no_parcial(self):
        r = self.client.get(self.url, {'documento': '11440'})
        self.assertEqual(r.context['total'], 0)
        self.assertContains(r, 'No existe un paciente registrado con ese número de documento.')

    def test_los_limites_del_rango_son_inclusivos(self):
        dia = timezone.localdate().isoformat()
        c = ConsultaMedica.objects.create(
            paciente=self.paciente, medico=self.medico, fecha_consulta=timezone.now(), motivo='Hoy',
        )
        r = self.client.get(self.url, {'documento': '1144012345', 'fecha_desde': dia, 'fecha_hasta': dia})
        self.assertEqual(list(r.context['consultas']), [c])

    def test_paciente_sin_consultas_en_el_rango(self):
        r = self.client.get(self.url, {
            'documento': '1144012345', 'fecha_desde': self.dia(100), 'fecha_hasta': self.dia(90),
        })
        self.assertContains(r, 'No se encontraron consultas con esos criterios.')

    def test_documento_inexistente(self):
        r = self.client.get(self.url, {'documento': '000'})
        self.assertContains(r, 'No existe un paciente registrado con ese número de documento.')

    def test_fecha_invalida_no_rompe_la_pagina(self):
        r = self.client.get(self.url, {'fecha_desde': 'abc'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'La fecha «desde» no es válida')

    def test_rango_invertido_muestra_error(self):
        r = self.client.get(self.url, {'fecha_desde': self.dia(0), 'fecha_hasta': self.dia(5)})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'La fecha «hasta» no puede ser anterior a la fecha «desde».')

    def test_solo_medicos(self):
        self.client.force_login(self.recep)
        self.assertEqual(self.client.get(self.url, {'documento': '1'}).status_code, 302)


class CatalogosInicialesTests(TestCase):
    """Una base de datos nueva debe traer diagnósticos y medicamentos para poder registrar consultas."""

    def test_hay_diagnosticos_cie10_y_medicamentos_desde_el_inicio(self):
        self.assertGreaterEqual(Enfermedad.objects.exclude(codigo='').count(), 60)
        self.assertGreaterEqual(Medicamento.objects.count(), 40)

    def test_codigos_cie10_con_formato_valido_y_sin_repetir(self):
        codigos = list(Enfermedad.objects.exclude(codigo='').values_list('codigo', flat=True))
        for codigo in codigos:
            self.assertRegex(codigo, r'^[A-Z]\d{2}(\.\d{1,2})?$', codigo)
        self.assertEqual(len(codigos), len(set(codigos)))

    def test_todos_activos_y_con_nombre(self):
        self.assertFalse(Enfermedad.objects.filter(activo=False).exists())
        self.assertFalse(Medicamento.objects.filter(activo=False).exists())
        self.assertFalse(Enfermedad.objects.filter(nombre='').exists())

    def test_los_selectores_de_la_consulta_los_ofrecen(self):
        from .forms import ConsultaMedicaForm
        form = ConsultaMedicaForm()
        self.assertGreaterEqual(form.fields['enfermedades'].queryset.count(), 60)
        self.assertGreaterEqual(form.fields['medicamentos'].queryset.count(), 40)
