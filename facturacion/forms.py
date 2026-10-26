import re

from django import forms

from pacientes.forms import ResaltarErroresMixin

from .models import AtencionEPS, Pago
from .tarifas import cuota_moderadora

class PagoForm(ResaltarErroresMixin, forms.ModelForm):
    """
    RF-14: datos que captura el recepcionista al cobrar una consulta particular.
    El valor no se digita: el sistema cobra la tarifa de la consulta (facturacion/tarifas.py).
    """

    class Meta:
        model = Pago
        fields = ['metodo_pago', 'observaciones']
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
    """
    RF-15: datos que captura el recepcionista al registrar una atención EPS.
    Los valores no se digitan: el paciente paga la cuota moderadora y el resto
    se factura a su EPS (facturacion/tarifas.py).
    """

    class Meta:
        model = AtencionEPS
        fields = ['numero_autorizacion', 'metodo_pago_cuota', 'observaciones']
        labels = {'metodo_pago_cuota': 'Método de pago de la cuota moderadora'}
        widgets = {
            'metodo_pago_cuota': forms.Select(attrs={
                'class': 'form-select', 'data-msg-requerido': 'Selecciona cómo pagó el paciente la cuota moderadora.',
            }),
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
            'metodo_pago_cuota': {
                'invalid_choice': 'Selecciona un método de pago válido de la lista.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campo = self.fields['metodo_pago_cuota']
        campo.choices = [('', 'Selecciona una opción')] + [c for c in campo.choices if c[0] != '']
        # Solo es obligatorio si el paciente realmente paga una cuota moderadora.
        campo.required = cuota_moderadora() > 0
        if campo.required:
            campo.error_messages['required'] = 'Selecciona cómo pagó el paciente la cuota moderadora.'

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
