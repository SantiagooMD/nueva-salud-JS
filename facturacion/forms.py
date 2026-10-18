import re

from django import forms

from pacientes.forms import ResaltarErroresMixin

from .models import AtencionEPS, Pago

MENSAJES_VALOR = {
    'required': 'Ingresa el valor en pesos.',
    'invalid': 'El valor debe ser un número, sin puntos, comas ni letras. Ej: 50000.',
    'max_decimal_places': 'El valor debe ser un número entero de pesos, sin decimales.',
    'max_digits': 'El valor es demasiado grande: máximo 12 dígitos.',
    'min_value': 'El valor debe ser mayor a $0.',
}


def _campo_valor(etiqueta, ayuda):
    return forms.DecimalField(
        label=etiqueta, min_value=1, max_digits=12, decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'min': 1, 'step': 1, 'placeholder': 'Ej: 50000',
            # Reglas para la validación en tiempo real (static/js/validacion.js)
            'data-msg-requerido': MENSAJES_VALOR['required'],
            'data-msg-min': MENSAJES_VALOR['min_value'],
            'data-msg-paso': MENSAJES_VALOR['max_decimal_places'],
            'data-msg-invalido': MENSAJES_VALOR['invalid'],
        }),
        help_text=ayuda, error_messages=MENSAJES_VALOR,
    )


class PagoForm(ResaltarErroresMixin, forms.ModelForm):
    """RF-14: datos que captura el recepcionista al cobrar una consulta particular."""

    valor = _campo_valor('Valor cobrado (COP)', 'Valor recibido del paciente, en pesos colombianos.')

    class Meta:
        model = Pago
        fields = ['valor', 'metodo_pago', 'observaciones']
        widgets = {
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select', 'data-msg-requerido': 'Selecciona el método de pago.',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'maxlength': 500,
                'placeholder': 'Opcional',
            }),
        }
        error_messages = {
            'metodo_pago': {
                'required': 'Selecciona el método de pago.',
                'invalid_choice': 'Selecciona un método de pago válido de la lista.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metodo_pago'].choices = [('', 'Selecciona una opción')] + [
            c for c in self.fields['metodo_pago'].choices if c[0] != ''
        ]

    def clean_observaciones(self):
        return self.cleaned_data.get('observaciones', '').strip()


class AtencionEPSForm(ResaltarErroresMixin, forms.ModelForm):
    """RF-15: datos que captura el recepcionista al registrar una atención EPS."""

    valor_facturable = _campo_valor(
        'Valor facturable a la EPS (COP)', 'Se factura a la EPS; no se cobra al paciente.',
    )

    class Meta:
        model = AtencionEPS
        fields = ['numero_autorizacion', 'valor_facturable', 'observaciones']
        widgets = {
            'numero_autorizacion': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 30, 'placeholder': 'Ej: AUT-2026-00123',
                'pattern': r'[A-Za-z0-9\/\-]+',  # escapado para que Chrome (modo /v) lo acepte
                'data-msg-patron': 'El número de autorización solo puede tener letras, números, guiones y barras, sin espacios.',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'maxlength': 500,
                'placeholder': 'Opcional',
            }),
        }
        error_messages = {
            'numero_autorizacion': {
                'max_length': 'El número de autorización no puede tener más de 30 caracteres.',
            },
        }

    def clean_numero_autorizacion(self):
        numero = self.cleaned_data.get('numero_autorizacion', '').strip()
        if numero and not re.fullmatch(r'[A-Za-z0-9\-/]+', numero):
            raise forms.ValidationError(
                'El número de autorización solo puede tener letras, números, guiones y barras, sin espacios.'
            )
        return numero

    def clean_observaciones(self):
        return self.cleaned_data.get('observaciones', '').strip()


class RangoFechasForm(ResaltarErroresMixin, forms.Form):
    """RF-16: rango de fechas del resumen financiero."""

    desde = forms.DateField(
        label='Desde',
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
            'data-msg-requerido': 'Selecciona la fecha de inicio del rango.',
            'data-msg-invalido': 'La fecha de inicio no es válida. Usa el selector de fecha.',
        }, format='%Y-%m-%d'),
        error_messages={
            'required': 'Selecciona la fecha de inicio del rango.',
            'invalid': 'La fecha de inicio no es válida. Usa el selector de fecha.',
        },
    )
    hasta = forms.DateField(
        label='Hasta',
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
            'data-min-campo': 'id_desde',
            'data-msg-requerido': 'Selecciona la fecha final del rango.',
            'data-msg-min': 'La fecha final no puede ser anterior a la fecha de inicio.',
            'data-msg-invalido': 'La fecha final no es válida. Usa el selector de fecha.',
        }, format='%Y-%m-%d'),
        error_messages={
            'required': 'Selecciona la fecha final del rango.',
            'invalid': 'La fecha final no es válida. Usa el selector de fecha.',
        },
    )

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get('desde'), datos.get('hasta')
        if desde and hasta and desde > hasta:
            self.add_error('hasta', 'La fecha final no puede ser anterior a la fecha de inicio.')
        return datos


class FiltroRegistrosForm(ResaltarErroresMixin, forms.Form):
    """Filtros opcionales del listado de pagos y atenciones: paciente (documento o nombre) y fechas."""

    q = forms.CharField(
        label='Paciente', required=False, max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Documento o nombre del paciente...',
        }),
    )
    desde = forms.DateField(
        label='Desde', required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
            'data-msg-invalido': 'La fecha «desde» no es válida. Usa el selector de fecha.',
        }, format='%Y-%m-%d'),
        error_messages={'invalid': 'La fecha «desde» no es válida. Usa el selector de fecha.'},
    )
    hasta = forms.DateField(
        label='Hasta', required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
            'data-min-campo': 'id_desde',
            'data-msg-min': 'La fecha «hasta» no puede ser anterior a la fecha «desde».',
            'data-msg-invalido': 'La fecha «hasta» no es válida. Usa el selector de fecha.',
        }, format='%Y-%m-%d'),
        error_messages={'invalid': 'La fecha «hasta» no es válida. Usa el selector de fecha.'},
    )

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get('desde'), datos.get('hasta')
        if desde and hasta and desde > hasta:
            self.add_error('hasta', 'La fecha «hasta» no puede ser anterior a la fecha «desde».')
        return datos
