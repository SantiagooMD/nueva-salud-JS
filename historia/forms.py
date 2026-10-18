from datetime import timedelta

from django import forms
from django.core.validators import MaxLengthValidator
from django.utils import timezone

from catalogos.models import Enfermedad, Medicamento
from pacientes.forms import ResaltarErroresMixin
from .models import ConsultaMedica

LIMITE_TEXTO = 2000  # caracteres máximos en síntomas, tratamiento y observaciones


class ConsultaMedicaForm(ResaltarErroresMixin, forms.ModelForm):
    class Meta:
        model = ConsultaMedica
        fields = [
            'fecha_consulta',
            'motivo',
            'sintomas',
            'enfermedades',
            'medicamentos',
            'tratamiento',
            'observaciones',
        ]
        widgets = {
            'fecha_consulta': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local',
                    # Reglas para la validación en tiempo real (static/js/validacion.js)
                    'data-max-ahora': '',
                    'data-msg-requerido': 'Ingresa la fecha y hora de la consulta.',
                    'data-msg-max': 'La fecha de la consulta no puede ser posterior a la fecha y hora actual.',
                    'data-msg-invalido': 'La fecha de la consulta no es válida. Usa el selector de fecha y hora.',
                },
                format='%Y-%m-%dT%H:%M',
            ),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Control, dolor de garganta, fiebre...',
                'minlength': 3,
                'maxlength': 300,
                'data-msg-requerido': 'Ingresa el motivo de la consulta.',
                'data-msg-corto': 'El motivo debe tener al menos 3 caracteres.',
            }),
            'sintomas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': LIMITE_TEXTO,
                'placeholder': 'Descripción de síntomas y hallazgos',
            }),
            'enfermedades': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '6',
            }),
            'medicamentos': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '6',
            }),
            'tratamiento': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': LIMITE_TEXTO,
                'placeholder': 'Indicaciones, dosis, recomendaciones',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'maxlength': LIMITE_TEXTO,
            }),
        }
        labels = {
            'enfermedades': 'Diagnósticos (seleccionar)',
            'medicamentos': 'Medicamentos (seleccionar)',
            'sintomas': 'Síntomas / anamnesis',
        }
        error_messages = {
            'fecha_consulta': {
                'required': 'Ingresa la fecha y hora de la consulta.',
                'invalid': 'La fecha de la consulta no es válida. Usa el selector de fecha y hora.',
            },
            'motivo': {
                'required': 'Ingresa el motivo de la consulta.',
                'max_length': 'El motivo no puede tener más de 300 caracteres.',
            },
            'enfermedades': {
                'invalid_choice': 'Uno de los diagnósticos seleccionados no está disponible. Elige solo de la lista.',
                'invalid_pk_value': 'Uno de los diagnósticos seleccionados no es válido. Elige solo de la lista.',
            },
            'medicamentos': {
                'invalid_choice': 'Uno de los medicamentos seleccionados no está disponible. Elige solo de la lista.',
                'invalid_pk_value': 'Uno de los medicamentos seleccionados no es válido. Elige solo de la lista.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['enfermedades'].queryset = Enfermedad.objects.filter(activo=True)
        self.fields['medicamentos'].queryset = Medicamento.objects.filter(activo=True)
        self.fields['enfermedades'].help_text = 'Mantén Ctrl (o Cmd) para seleccionar varias.'
        self.fields['medicamentos'].help_text = 'Mantén Ctrl (o Cmd) para seleccionar varios.'
        self.fields['fecha_consulta'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']
        for nombre in ('sintomas', 'tratamiento', 'observaciones'):
            self.fields[nombre].validators.append(MaxLengthValidator(
                LIMITE_TEXTO, message=f'No puede tener más de {LIMITE_TEXTO} caracteres.',
            ))
        if not self.instance.pk:
            self.initial.setdefault('fecha_consulta', timezone.localtime().strftime('%Y-%m-%dT%H:%M'))

    def clean_fecha_consulta(self):
        fecha = self.cleaned_data['fecha_consulta']
        # Pequeña tolerancia por si el reloj del computador va unos minutos adelantado.
        if fecha > timezone.now() + timedelta(minutes=5):
            raise forms.ValidationError(
                'La fecha de la consulta no puede ser posterior a la fecha y hora actual.'
            )
        return fecha

    def clean_motivo(self):
        motivo = ' '.join(self.cleaned_data['motivo'].split())
        if len(motivo) < 3:
            raise forms.ValidationError('El motivo debe tener al menos 3 caracteres.')
        return motivo
