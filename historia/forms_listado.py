import re

from django import forms

from pacientes.forms import ResaltarErroresMixin


class FiltroConsultasForm(ResaltarErroresMixin, forms.Form):
    """
    RF-12: listado de consultas realizadas a un paciente, con dos criterios de búsqueda:
    el número de documento del paciente (obligatorio, identifica al paciente) y un rango de
    fechas (opcional: sin fechas se listan todas las consultas del paciente).
    """

    documento = forms.CharField(
        label='Número de documento', required=True, max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Ej: 1144012345', 'maxlength': 20,
            'pattern': '[A-Za-z0-9]+',
            'data-msg-requerido': 'Ingresa el número de documento del paciente.',
            'data-msg-patron': 'El documento solo puede contener letras y números, sin espacios ni símbolos.',
        }),
        error_messages={
            'required': 'Ingresa el número de documento del paciente.',
            'max_length': 'El número de documento no puede tener más de 20 caracteres.',
        },
    )
    fecha_desde = forms.DateField(
        label='Fecha desde', required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
            'data-msg-invalido': 'La fecha «desde» no es válida. Usa el selector de fecha.',
        }, format='%Y-%m-%d'),
        error_messages={'invalid': 'La fecha «desde» no es válida. Usa el selector de fecha.'},
    )
    fecha_hasta = forms.DateField(
        label='Fecha hasta', required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
            'data-min-campo': 'id_fecha_desde',
            'data-msg-min': 'La fecha «hasta» no puede ser anterior a la fecha «desde».',
            'data-msg-invalido': 'La fecha «hasta» no es válida. Usa el selector de fecha.',
        }, format='%Y-%m-%d'),
        error_messages={'invalid': 'La fecha «hasta» no es válida. Usa el selector de fecha.'},
    )

    def clean_documento(self):
        documento = self.cleaned_data.get('documento', '').strip()
        if documento and not re.fullmatch(r'[A-Za-z0-9]+', documento):
            raise forms.ValidationError(
                'El documento solo puede contener letras y números, sin espacios ni símbolos.'
            )
        return documento

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get('fecha_desde'), datos.get('fecha_hasta')
        if desde and hasta and desde > hasta:
            self.add_error('fecha_hasta', 'La fecha «hasta» no puede ser anterior a la fecha «desde».')
        return datos
