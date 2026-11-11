import re

from django import forms

from pacientes.forms import ResaltarErroresMixin

from .models import AtencionEPS, Pago
from .tarifas import cuota_moderadora, tarifa_consulta

class PagoForm(ResaltarErroresMixin, forms.ModelForm):
    """
    RF-14: cobro de consulta particular.
    El valor no se digita: se cobra la tarifa del sistema.
    Según el método de pago se piden datos reales del recaudo.
    """

    class Meta:
        model = Pago
        fields = [
            'metodo_pago',
            'tipo_tarjeta', 'franquicia', 'ultimos_digitos', 'numero_aprobacion',
            'entidad_transferencia', 'referencia_transferencia',
            'valor_recibido',
            'observaciones',
        ]
        widgets = {
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_metodo_pago',
                'data-msg-requerido': 'Selecciona el método de pago.',
            }),
            'tipo_tarjeta': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_tarjeta'}),
            'franquicia': forms.Select(attrs={'class': 'form-select', 'id': 'id_franquicia'}),
            'ultimos_digitos': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'id_ultimos_digitos',
                'maxlength': 4, 'inputmode': 'numeric', 'placeholder': 'Ej: 1234',
            }),
            'numero_aprobacion': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'id_numero_aprobacion',
                'maxlength': 30, 'placeholder': 'Ej: 845221',
            }),
            'entidad_transferencia': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_entidad_transferencia',
            }),
            'referencia_transferencia': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'id_referencia_transferencia',
                'maxlength': 40, 'placeholder': 'Ej: 00918273645',
            }),
            'valor_recibido': forms.NumberInput(attrs={
                'class': 'form-control', 'id': 'id_valor_recibido',
                'min': 0, 'step': 1, 'placeholder': 'Ej: 100000',
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
        for nombre in ('tipo_tarjeta', 'franquicia', 'entidad_transferencia'):
            campo = self.fields[nombre]
            campo.required = False
            campo.choices = [('', 'Selecciona una opción')] + [c for c in campo.choices if c[0] != '']
        for nombre in ('ultimos_digitos', 'numero_aprobacion', 'referencia_transferencia', 'valor_recibido'):
            self.fields[nombre].required = False

    def clean_observaciones(self):
        return self.cleaned_data.get('observaciones', '').strip()

    def clean_ultimos_digitos(self):
        valor = (self.cleaned_data.get('ultimos_digitos') or '').strip()
        if valor and not re.fullmatch(r'\d{4}', valor):
            raise forms.ValidationError('Escribe solo los últimos 4 dígitos de la tarjeta, sin espacios.')
        return valor

    def clean_numero_aprobacion(self):
        valor = (self.cleaned_data.get('numero_aprobacion') or '').strip()
        if valor and not re.fullmatch(r'[A-Za-z0-9\-]+', valor):
            raise forms.ValidationError('El número de aprobación solo puede tener letras, números y guiones.')
        return valor

    def clean_referencia_transferencia(self):
        valor = (self.cleaned_data.get('referencia_transferencia') or '').strip()
        if valor and not re.fullmatch(r'[A-Za-z0-9\-]+', valor):
            raise forms.ValidationError('La referencia solo puede tener letras, números y guiones.')
        return valor

    def clean(self):
        datos = super().clean()
        metodo = datos.get('metodo_pago')
        self._vaciar_detalle(datos)

        if metodo == Pago.MetodoPago.TARJETA:
            if not datos.get('tipo_tarjeta'):
                self.add_error('tipo_tarjeta', 'Indica si la tarjeta es débito o crédito.')
            if not datos.get('franquicia'):
                self.add_error('franquicia', 'Selecciona la franquicia de la tarjeta.')
            if not datos.get('ultimos_digitos'):
                self.add_error('ultimos_digitos', 'Ingresa los últimos 4 dígitos de la tarjeta.')
            if not datos.get('numero_aprobacion'):
                self.add_error('numero_aprobacion', 'Ingresa el número de aprobación del datáfono.')
        elif metodo == Pago.MetodoPago.TRANSFERENCIA:
            if not datos.get('entidad_transferencia'):
                self.add_error('entidad_transferencia', 'Selecciona la entidad de la transferencia.')
            if not datos.get('referencia_transferencia'):
                self.add_error('referencia_transferencia', 'Ingresa el número de referencia de la transferencia.')
        elif metodo == Pago.MetodoPago.EFECTIVO:
            recibido = datos.get('valor_recibido')
            if recibido is None:
                self.add_error('valor_recibido', 'Ingresa el valor en efectivo que entregó el paciente.')
            elif recibido < tarifa_consulta():
                self.add_error('valor_recibido', 'El valor recibido no puede ser menor que el valor de la consulta.')
            else:
                datos['valor_devuelto'] = recibido - tarifa_consulta()
        return datos

    def _vaciar_detalle(self, datos):
        metodo = datos.get('metodo_pago')
        if metodo != Pago.MetodoPago.TARJETA:
            datos['tipo_tarjeta'] = ''
            datos['franquicia'] = ''
            datos['ultimos_digitos'] = ''
            datos['numero_aprobacion'] = ''
        if metodo != Pago.MetodoPago.TRANSFERENCIA:
            datos['entidad_transferencia'] = ''
            datos['referencia_transferencia'] = ''
        if metodo != Pago.MetodoPago.EFECTIVO:
            datos['valor_recibido'] = None
            datos['valor_devuelto'] = None

    def save(self, commit=True):
        pago = super().save(commit=False)
        pago.valor_devuelto = self.cleaned_data.get('valor_devuelto')
        if commit:
            pago.save()
        return pago


class AtencionEPSForm(ResaltarErroresMixin, forms.ModelForm):
    """
    RF-15: atención EPS.
    El paciente solo paga la cuota moderadora. El resto se factura a la EPS.
    """

    class Meta:
        model = AtencionEPS
        fields = [
            'numero_autorizacion', 'numero_radicado', 'metodo_pago_cuota',
            'tipo_tarjeta', 'franquicia', 'ultimos_digitos', 'numero_aprobacion',
            'entidad_transferencia', 'referencia_transferencia',
            'valor_recibido',
            'observaciones',
        ]
        labels = {'metodo_pago_cuota': 'Método de pago de la cuota moderadora'}
        widgets = {
            'metodo_pago_cuota': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_metodo_pago_cuota',
                'data-msg-requerido': 'Selecciona cómo pagó el paciente la cuota moderadora.',
            }),
            'numero_autorizacion': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 30, 'placeholder': 'Ej: AUT-2026-00123',
                'pattern': r'[A-Za-z0-9\/\-]+',
                'data-msg-patron': 'El número de autorización solo puede tener letras, números, guiones y barras, sin espacios.',
            }),
            'numero_radicado': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 40, 'placeholder': 'Ej: RAD-2026-00458',
            }),
            'tipo_tarjeta': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_tarjeta'}),
            'franquicia': forms.Select(attrs={'class': 'form-select', 'id': 'id_franquicia'}),
            'ultimos_digitos': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'id_ultimos_digitos',
                'maxlength': 4, 'inputmode': 'numeric', 'placeholder': 'Ej: 1234',
            }),
            'numero_aprobacion': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'id_numero_aprobacion',
                'maxlength': 30, 'placeholder': 'Ej: 845221',
            }),
            'entidad_transferencia': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_entidad_transferencia',
            }),
            'referencia_transferencia': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'id_referencia_transferencia',
                'maxlength': 40, 'placeholder': 'Ej: 00918273645',
            }),
            'valor_recibido': forms.NumberInput(attrs={
                'class': 'form-control', 'id': 'id_valor_recibido',
                'min': 0, 'step': 1, 'placeholder': 'Ej: 10000',
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
        campo.required = cuota_moderadora() > 0
        if campo.required:
            campo.error_messages['required'] = 'Selecciona cómo pagó el paciente la cuota moderadora.'
        for nombre in ('tipo_tarjeta', 'franquicia', 'entidad_transferencia'):
            extra = self.fields[nombre]
            extra.required = False
            extra.choices = [('', 'Selecciona una opción')] + [c for c in extra.choices if c[0] != '']
        for nombre in (
            'numero_autorizacion', 'numero_radicado', 'ultimos_digitos',
            'numero_aprobacion', 'referencia_transferencia', 'valor_recibido',
        ):
            self.fields[nombre].required = False

    def clean_numero_autorizacion(self):
        numero = (self.cleaned_data.get('numero_autorizacion') or '').strip()
        if numero and not re.fullmatch(r'[A-Za-z0-9\-/]+', numero):
            raise forms.ValidationError(
                'El número de autorización solo puede tener letras, números, guiones y barras, sin espacios.'
            )
        return numero

    def clean_numero_radicado(self):
        numero = (self.cleaned_data.get('numero_radicado') or '').strip()
        if numero and not re.fullmatch(r'[A-Za-z0-9\-/]+', numero):
            raise forms.ValidationError(
                'El radicado solo puede tener letras, números, guiones y barras, sin espacios.'
            )
        return numero

    def clean_ultimos_digitos(self):
        valor = (self.cleaned_data.get('ultimos_digitos') or '').strip()
        if valor and not re.fullmatch(r'\d{4}', valor):
            raise forms.ValidationError('Escribe solo los últimos 4 dígitos de la tarjeta, sin espacios.')
        return valor

    def clean_numero_aprobacion(self):
        valor = (self.cleaned_data.get('numero_aprobacion') or '').strip()
        if valor and not re.fullmatch(r'[A-Za-z0-9\-]+', valor):
            raise forms.ValidationError('El número de aprobación solo puede tener letras, números y guiones.')
        return valor

    def clean_referencia_transferencia(self):
        valor = (self.cleaned_data.get('referencia_transferencia') or '').strip()
        if valor and not re.fullmatch(r'[A-Za-z0-9\-]+', valor):
            raise forms.ValidationError('La referencia solo puede tener letras, números y guiones.')
        return valor

    def clean_observaciones(self):
        return (self.cleaned_data.get('observaciones') or '').strip()

    def clean(self):
        datos = super().clean()
        metodo = datos.get('metodo_pago_cuota')
        cuota = cuota_moderadora()
        self._vaciar_detalle(datos, metodo)

        if cuota <= 0:
            datos['metodo_pago_cuota'] = ''
            self._vaciar_detalle(datos, '')
            return datos

        if metodo == Pago.MetodoPago.TARJETA:
            if not datos.get('tipo_tarjeta'):
                self.add_error('tipo_tarjeta', 'Indica si la tarjeta es débito o crédito.')
            if not datos.get('franquicia'):
                self.add_error('franquicia', 'Selecciona la franquicia de la tarjeta.')
            if not datos.get('ultimos_digitos'):
                self.add_error('ultimos_digitos', 'Ingresa los últimos 4 dígitos de la tarjeta.')
            if not datos.get('numero_aprobacion'):
                self.add_error('numero_aprobacion', 'Ingresa el número de aprobación del datáfono.')
        elif metodo == Pago.MetodoPago.TRANSFERENCIA:
            if not datos.get('entidad_transferencia'):
                self.add_error('entidad_transferencia', 'Selecciona la entidad de la transferencia.')
            if not datos.get('referencia_transferencia'):
                self.add_error('referencia_transferencia', 'Ingresa el número de referencia de la transferencia.')
        elif metodo == Pago.MetodoPago.EFECTIVO:
            recibido = datos.get('valor_recibido')
            if recibido is None:
                self.add_error('valor_recibido', 'Ingresa el valor en efectivo que entregó el paciente.')
            elif recibido < cuota:
                self.add_error('valor_recibido', 'El valor recibido no puede ser menor que la cuota moderadora.')
            else:
                datos['valor_devuelto'] = recibido - cuota
        return datos

    def _vaciar_detalle(self, datos, metodo):
        if metodo != Pago.MetodoPago.TARJETA:
            datos['tipo_tarjeta'] = ''
            datos['franquicia'] = ''
            datos['ultimos_digitos'] = ''
            datos['numero_aprobacion'] = ''
        if metodo != Pago.MetodoPago.TRANSFERENCIA:
            datos['entidad_transferencia'] = ''
            datos['referencia_transferencia'] = ''
        if metodo != Pago.MetodoPago.EFECTIVO:
            datos['valor_recibido'] = None
            datos['valor_devuelto'] = None

    def save(self, commit=True):
        atencion = super().save(commit=False)
        atencion.valor_devuelto = self.cleaned_data.get('valor_devuelto')
        if commit:
            atencion.save()
        return atencion


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
    tipo = forms.ChoiceField(
        label='Tipo de paciente',
        choices=[
            ('TODOS', 'Todos'),
            ('PARTICULAR', 'Solo particulares'),
            ('EPS', 'Solo EPS'),
        ],
        required=False,
        initial='TODOS',
        widget=forms.Select(attrs={'class': 'form-select'}),
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
