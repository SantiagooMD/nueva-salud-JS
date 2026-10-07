from django.conf import settings
from django.db import models

from catalogos.models import Enfermedad, Medicamento
from pacientes.models import Paciente


class ConsultaMedica(models.Model):
    """
    Registro de una consulta médica (historia clínica del paciente).
    Sprint 2: registrar, actualizar y consultar historial.
    Diagnósticos y medicamentos se seleccionan del catálogo.
    """
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='consultas',
        verbose_name='Paciente',
    )
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='consultas_realizadas',
        verbose_name='Médico',
    )
    fecha_consulta = models.DateTimeField(verbose_name='Fecha de la consulta')
    motivo = models.CharField(max_length=300, verbose_name='Motivo de consulta')
    sintomas = models.TextField(blank=True, verbose_name='Síntomas / anamnesis')
    enfermedades = models.ManyToManyField(
        Enfermedad,
        blank=True,
        related_name='consultas',
        verbose_name='Diagnósticos (enfermedades)',
    )
    medicamentos = models.ManyToManyField(
        Medicamento,
        blank=True,
        related_name='consultas',
        verbose_name='Medicamentos recetados',
    )
    tratamiento = models.TextField(blank=True, verbose_name='Tratamiento / indicaciones')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consulta médica'
        verbose_name_plural = 'Consultas médicas'
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f'Consulta {self.paciente} - {self.fecha_consulta:%d/%m/%Y %H:%M}'
