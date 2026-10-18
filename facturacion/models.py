from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from historia.models import ConsultaMedica


class Pago(models.Model):
    """
    RF-14: Registrar Pago de Paciente Particular.
    Cada consulta de un paciente particular tiene como máximo un pago.
    Valores en pesos colombianos (COP), sin decimales.
    """

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TARJETA = 'TARJETA', 'Tarjeta débito o crédito'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia (Nequi, Daviplata, PSE)'

    consulta = models.OneToOneField(
        ConsultaMedica, on_delete=models.PROTECT, related_name='pago',
        verbose_name='Consulta',
    )
    valor = models.DecimalField(
        max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
        verbose_name='Valor cobrado (COP)',
    )
    metodo_pago = models.CharField(
        max_length=15, choices=MetodoPago.choices, verbose_name='Método de pago',
    )
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='pagos_registrados', verbose_name='Registrado por',
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha del pago')

    class Meta:
        verbose_name = 'Pago de paciente particular'
        verbose_name_plural = 'Pagos de pacientes particulares'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f'{self.numero} - {self.consulta.paciente.nombre_completo}'

    @property
    def numero(self):
        return f'PAG-{self.pk:06d}' if self.pk else 'PAG-—'


class AtencionEPS(models.Model):
    """
    RF-15: Registrar Atención de Paciente EPS.
    La atención se factura a la EPS; al paciente no se le cobra directamente.
    """

    consulta = models.OneToOneField(
        ConsultaMedica, on_delete=models.PROTECT, related_name='atencion_eps',
        verbose_name='Consulta',
    )
    # Copia del nombre de la EPS al momento de la atención, para que el registro
    # no cambie si después se actualiza la afiliación del paciente.
    eps = models.CharField(max_length=100, verbose_name='EPS')
    numero_autorizacion = models.CharField(
        max_length=30, blank=True, verbose_name='Número de autorización',
    )
    valor_facturable = models.DecimalField(
        max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
        verbose_name='Valor facturable a la EPS (COP)',
    )
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='atenciones_eps_registradas', verbose_name='Registrado por',
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        verbose_name = 'Atención de paciente EPS'
        verbose_name_plural = 'Atenciones de pacientes EPS'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f'{self.codigo} - {self.consulta.paciente.nombre_completo}'

    @property
    def codigo(self):
        return f'ATN-{self.pk:06d}' if self.pk else 'ATN-—'
