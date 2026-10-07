from django import forms
from django.utils import timezone

from catalogos.models import Enfermedad, Medicamento
from .models import ConsultaMedica


class ConsultaMedicaForm(forms.ModelForm):
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
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Control, dolor de garganta, fiebre...',
            }),
            'sintomas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
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
                'placeholder': 'Indicaciones, dosis, recomendaciones',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['enfermedades'].queryset = Enfermedad.objects.filter(activo=True)
        self.fields['medicamentos'].queryset = Medicamento.objects.filter(activo=True)
        self.fields['enfermedades'].help_text = 'Mantén Ctrl (o Cmd) para seleccionar varias.'
        self.fields['medicamentos'].help_text = 'Mantén Ctrl (o Cmd) para seleccionar varios.'
        self.fields['fecha_consulta'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']
        if not self.instance.pk:
            self.initial.setdefault('fecha_consulta', timezone.localtime().strftime('%Y-%m-%dT%H:%M'))