from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Paciente

DATOS_VALIDOS = {
    'tipo_documento': 'CC',
    'numero_documento': '1144012345',
    'nombres': 'María José',
    'apellidos': 'Pérez Gómez',
    'fecha_nacimiento': '1995-04-12',
    'genero': 'F',
    'telefono': '3001234567',
    'direccion': 'Calle 10 # 5-20',
    'email': 'maria@correo.com',
    'tipo_afiliacion': 'PARTICULAR',
    'nombre_eps': '',
}


class BaseTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='recep', password='clave12345')
        self.client.login(username='recep', password='clave12345')


class RegistrarPacienteTests(BaseTest):
    url = 'registrar_paciente'

    def post(self, **cambios):
        datos = {**DATOS_VALIDOS, **cambios}
        return self.client.post(reverse(self.url), datos)

    def test_registro_valido(self):
        r = self.post()
        self.assertRedirects(r, reverse('consultar_paciente'))
        self.assertTrue(Paciente.objects.filter(numero_documento='1144012345').exists())

    def test_campos_vacios_muestran_error_por_campo(self):
        r = self.client.post(reverse(self.url), {'tipo_documento': 'CC', 'tipo_afiliacion': 'PARTICULAR'})
        self.assertEqual(r.status_code, 200)
        errores = r.context['form'].errors
        for campo in ['numero_documento', 'nombres', 'apellidos', 'fecha_nacimiento', 'genero']:
            self.assertIn(campo, errores)
        self.assertContains(r, 'Ingresa el número de documento del paciente.')
        self.assertContains(r, 'Selecciona el género del paciente.')
        self.assertContains(r, 'is-invalid')
        self.assertFalse(Paciente.objects.exists())

    def test_documento_no_numerico(self):
        r = self.post(numero_documento='12A45')
        self.assertContains(r, 'solo puede contener dígitos')

    def test_documento_duplicado(self):
        self.post()
        r = self.post()
        self.assertContains(r, 'Ya existe un paciente registrado con este número de documento.')

    def test_nombre_con_numeros(self):
        r = self.post(nombres='Ana123')
        self.assertContains(r, 'solo puede contener letras')

    def test_fecha_futura(self):
        r = self.post(fecha_nacimiento=(date.today() + timedelta(days=1)).isoformat())
        self.assertContains(r, 'no puede ser posterior a hoy')

    def test_telefono_invalido_y_email_invalido(self):
        r = self.post(telefono='abc', email='no-es-correo')
        self.assertContains(r, 'El teléfono debe tener entre 7 y 15 dígitos')
        self.assertContains(r, 'El correo no es válido')

    def test_eps_requiere_nombre(self):
        r = self.post(tipo_afiliacion='EPS', nombre_eps='')
        self.assertContains(r, 'Indica el nombre de la EPS del paciente.')

    def test_particular_limpia_eps(self):
        self.post(nombre_eps='Sura')
        self.assertEqual(Paciente.objects.get().nombre_eps, '')

    def test_campos_opcionales_pueden_ir_vacios(self):
        r = self.post(telefono='', direccion='', email='')
        self.assertRedirects(r, reverse('consultar_paciente'))


class BuscarParaConsultaTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.p = Paciente.objects.create(
            tipo_documento='CC', numero_documento='1144012345', nombres='María José',
            apellidos='Pérez Gómez', fecha_nacimiento=date(1995, 4, 12), genero='F',
        )
        Paciente.objects.create(
            tipo_documento='CC', numero_documento='999888', nombres='Carlos',
            apellidos='Ruiz', fecha_nacimiento=date(1980, 1, 1), genero='M', activo=False,
        )

    def buscar(self, q):
        return self.client.get(reverse('buscar_para_consulta'), {'q': q})

    def test_busca_por_documento(self):
        self.assertEqual(self.buscar('1144012345').context['pacientes'], [self.p])

    def test_busca_por_nombre_sin_tildes_y_por_partes(self):
        self.assertEqual(self.buscar('maria').context['pacientes'], [self.p])
        self.assertEqual(self.buscar('perez gomez').context['pacientes'], [self.p])
        self.assertEqual(self.buscar('pérez maría').context['pacientes'], [self.p])

    def test_no_muestra_inactivos_ni_inexistentes(self):
        self.assertEqual(self.buscar('Carlos').context['pacientes'], [])
        r = self.buscar('zzzz')
        self.assertContains(r, 'No se encontró ningún paciente activo')

    def test_iniciar_consulta_muestra_exito(self):
        r = self.client.post(reverse('iniciar_consulta', args=[self.p.pk]), follow=True)
        self.assertContains(r, 'Consulta iniciada con éxito')
        self.assertContains(r, 'alert-success')

    def test_iniciar_consulta_solo_post(self):
        r = self.client.get(reverse('iniciar_consulta', args=[self.p.pk]))
        self.assertEqual(r.status_code, 405)
