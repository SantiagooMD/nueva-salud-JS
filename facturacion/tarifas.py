"""
Tarifas de la consulta, tomadas de settings.py (TARIFA_CONSULTA y CUOTA_MODERADORA_EPS).

Regla de cobro (el sistema la aplica solo, según la afiliación del paciente):
  - Particular: paga la tarifa completa de la consulta.
  - EPS: paga en recepción únicamente la cuota moderadora; el resto se factura a la EPS.
"""
from decimal import Decimal

from django.conf import settings


def tarifa_consulta():
    return Decimal(str(getattr(settings, 'TARIFA_CONSULTA', 80000)))


def cuota_moderadora():
    cuota = Decimal(str(getattr(settings, 'CUOTA_MODERADORA_EPS', 5000)))
    return min(cuota, tarifa_consulta())


def valor_a_facturar_eps():
    """Parte de la consulta que paga la EPS: tarifa menos la cuota que paga el paciente."""
    return tarifa_consulta() - cuota_moderadora()
