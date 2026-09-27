from datetime import date

from django.db import models


class Paciente(models.Model):
    """
    Paciente del consultorio Nueva Salud JS.
    Cubre RF-03 (registrar), RF-04 (consultar), RF-05 (actualizar),
    RF-06 (inactivar), RF-07 (buscar para consulta) y RF-08 (clasificar EPS/Particular).
    """

    class TipoDocumento(models.TextChoices):
        CC = 'CC', 'Cédula de Ciudadanía'
        TI = 'TI', 'Tarjeta de Identidad'
        CE = 'CE', 'Cédula de Extranjería'
        PA = 'PA', 'Pasaporte'

    class Genero(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'
        OTRO = 'O', 'Otro'

    class TipoAfiliacion(models.TextChoices):
        EPS = 'EPS', 'EPS'
        PARTICULAR = 'PARTICULAR', 'Particular'

    tipo_documento = models.CharField(
        max_length=2, choices=TipoDocumento.choices, default=TipoDocumento.CC,
        verbose_name='Tipo de documento',
    )
    numero_documento = models.CharField(
        max_length=20, unique=True, verbose_name='Número de documento',
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(verbose_name='Fecha de nacimiento')
    genero = models.CharField(max_length=1, choices=Genero.choices)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)

    tipo_afiliacion = models.CharField(
        max_length=10, choices=TipoAfiliacion.choices,
        default=TipoAfiliacion.PARTICULAR, verbose_name='Tipo de afiliación',
    )
    nombre_eps = models.CharField(
        max_length=100, blank=True, verbose_name='Nombre de la EPS',
    )

    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.nombre_completo} ({self.numero_documento})'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def edad(self):
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
