from django import template

register = template.Library()


def formato_pesos(valor):
    """50000 -> '$50.000' (pesos colombianos: punto como separador de miles, sin decimales)."""
    try:
        return '$' + f'{int(valor):,}'.replace(',', '.')
    except (TypeError, ValueError):
        return '—'


register.filter('pesos', formato_pesos)
