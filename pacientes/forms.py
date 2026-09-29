import re
from datetime import date

from django import forms

from .models import Paciente

# Letras (con tildes y ñ), espacios, apostrofe y guion: sirve para nombres compuestos
# como "María José", "De la Cruz" o "O'Brien".
REGEX_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]*$")
REGEX_TELEFONO = re.compile(r'^\+?\d{7,15}$')


class ResaltarErroresMixin:
    """
    Después de validar, agrega la clase de Bootstrap `is-invalid` a cada campo con error
    para que se pinte en rojo, y `is-valid` a los que quedaron bien cuando el formulario
    fue enviado con errores en otros campos.
    """

    def full_clean(self):
        super().full_clean()
        if not self.is_bound:
            return
        for nombre, campo in self.fields.items():
            clases = campo.widget.attrs.get('class', '').split()
            if nombre in self.errors:
                clases.append('is-invalid')
            campo.widget.attrs['class'] = ' '.join(clases)


class PacienteForm(ResaltarErroresMixin, forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'tipo_documento', 'numero_documento', 'nombres', 'apellidos',
            'fecha_nacimiento', 'genero', 'telefono', 'direccion', 'email',
            'tipo_afiliacion', 'nombre_eps',
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 20, 'placeholder': 'Ej: 1144012345'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100, 'placeholder': 'Ej: María José'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100, 'placeholder': 'Ej: Pérez Gómez'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 20, 'inputmode': 'tel', 'placeholder': 'Ej: 3001234567'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200, 'placeholder': 'Ej: Calle 10 # 5-20'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: paciente@correo.com'}),
            'tipo_afiliacion': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_afiliacion'}),
            'nombre_eps': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre_eps', 'maxlength': 100, 'placeholder': 'Ej: Sura, Sanitas, Nueva EPS'}),
        }
        error_messages = {
            'tipo_documento': {
                'required': 'Selecciona el tipo de documento.',
                'invalid_choice': 'Selecciona un tipo de documento válido de la lista.',
            },
            'numero_documento': {
                'required': 'Ingresa el número de documento del paciente.',
                'max_length': 'El número de documento no puede tener más de 20 caracteres.',
                'unique': 'Ya existe un paciente registrado con este número de documento.',
            },
            'nombres': {
                'required': 'Ingresa los nombres del paciente.',
                'max_length': 'Los nombres no pueden tener más de 100 caracteres.',
            },
            'apellidos': {
                'required': 'Ingresa los apellidos del paciente.',
                'max_length': 'Los apellidos no pueden tener más de 100 caracteres.',
            },
            'fecha_nacimiento': {
                'required': 'Ingresa la fecha de nacimiento del paciente.',
                'invalid': 'La fecha de nacimiento no es válida. Usa el selector de fecha.',
            },
            'genero': {
                'required': 'Selecciona el género del paciente.',
                'invalid_choice': 'Selecciona un género válido de la lista.',
            },
            'email': {
                'invalid': 'El correo no es válido. Debe tener el formato nombre@dominio.com.',
                'max_length': 'El correo no puede tener más de 254 caracteres.',
            },
            'tipo_afiliacion': {
                'required': 'Selecciona el tipo de afiliación (EPS o Particular).',
                'invalid_choice': 'Selecciona un tipo de afiliación válido de la lista.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La opción vacía del género debe pedir una acción, no verse como un valor.
        self.fields['genero'].choices = [('', 'Selecciona una opción')] + [
            c for c in self.fields['genero'].choices if c[0] != ''
        ]

    # ---- Validaciones por campo -------------------------------------------------

    def clean_numero_documento(self):
        numero = self.cleaned_data['numero_documento'].strip().replace(' ', '')
        tipo = self.cleaned_data.get('tipo_documento')

        if not numero:
            raise forms.ValidationError('Ingresa el número de documento del paciente.')

        if tipo == Paciente.TipoDocumento.PA:
            if not numero.isalnum():
                raise forms.ValidationError('El pasaporte solo puede tener letras y números, sin símbolos.')
            if not 5 <= len(numero) <= 20:
                raise forms.ValidationError('El pasaporte debe tener entre 5 y 20 caracteres.')
        elif tipo:
            if not numero.isdigit():
                raise forms.ValidationError('El número de documento solo puede contener dígitos, sin puntos, letras ni espacios.')
            if not 5 <= len(numero) <= 15:
                raise forms.ValidationError('El número de documento debe tener entre 5 y 15 dígitos.')

        qs = Paciente.objects.filter(numero_documento__iexact=numero)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un paciente registrado con este número de documento.')
        return numero

    def _limpiar_nombre(self, campo, etiqueta):
        valor = ' '.join(self.cleaned_data[campo].split())
        if len(valor) < 2:
            raise forms.ValidationError(f'{etiqueta} debe tener al menos 2 letras.')
        if not REGEX_NOMBRE.match(valor):
            raise forms.ValidationError(f'{etiqueta} solo puede contener letras y espacios, sin números ni símbolos.')
        return valor

    def clean_nombres(self):
        return self._limpiar_nombre('nombres', 'Los nombres')

    def clean_apellidos(self):
        return self._limpiar_nombre('apellidos', 'Los apellidos')

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data['fecha_nacimiento']
        hoy = date.today()
        if fecha > hoy:
            raise forms.ValidationError('La fecha de nacimiento no puede ser posterior a hoy.')
        if fecha.year < hoy.year - 120:
            raise forms.ValidationError('La fecha de nacimiento no es válida: el paciente tendría más de 120 años.')
        return fecha

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not telefono:
            return ''
        limpio = re.sub(r'[\s\-().]', '', telefono)
        if not REGEX_TELEFONO.match(limpio):
            raise forms.ValidationError('El teléfono debe tener entre 7 y 15 dígitos, sin letras. Ej: 3001234567.')
        return limpio

    def clean_nombre_eps(self):
        return ' '.join(self.cleaned_data.get('nombre_eps', '').split())

    def clean(self):
        cleaned_data = super().clean()
        tipo_afiliacion = cleaned_data.get('tipo_afiliacion')
        nombre_eps = cleaned_data.get('nombre_eps')
        if tipo_afiliacion == Paciente.TipoAfiliacion.EPS and not nombre_eps:
            self.add_error('nombre_eps', 'Indica el nombre de la EPS del paciente.')
        elif tipo_afiliacion == Paciente.TipoAfiliacion.PARTICULAR:
            # Un paciente particular no debe quedar con una EPS guardada por error.
            cleaned_data['nombre_eps'] = ''
        return cleaned_data


class PacienteEditForm(ResaltarErroresMixin, forms.ModelForm):
    """
    RF-05: Actualizar Datos del Paciente.
    El SRS solo autoriza modificar nombre, teléfono, correo e información
    de contacto — el documento, la fecha de nacimiento y el género quedan
    fijos una vez registrado el paciente.
    """

    class Meta:
        model = Paciente
        fields = ['nombres', 'apellidos', 'telefono', 'email', 'direccion']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 20, 'inputmode': 'tel'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
        }
        error_messages = {
            'nombres': {'required': 'Ingresa los nombres del paciente.'},
            'apellidos': {'required': 'Ingresa los apellidos del paciente.'},
            'email': {'invalid': 'El correo no es válido. Debe tener el formato nombre@dominio.com.'},
        }

    clean_nombres = PacienteForm.clean_nombres
    clean_apellidos = PacienteForm.clean_apellidos
    clean_telefono = PacienteForm.clean_telefono
    _limpiar_nombre = PacienteForm._limpiar_nombre
