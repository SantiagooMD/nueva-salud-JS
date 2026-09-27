from django import forms

from .models import Paciente


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'tipo_documento', 'numero_documento', 'nombres', 'apellidos',
            'fecha_nacimiento', 'genero', 'telefono', 'direccion', 'email',
            'tipo_afiliacion', 'nombre_eps',
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tipo_afiliacion': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_afiliacion'}),
            'nombre_eps': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre_eps'}),
        }

    def clean_numero_documento(self):
        numero = self.cleaned_data['numero_documento'].strip()
        qs = Paciente.objects.filter(numero_documento=numero)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un paciente registrado con este número de documento.')
        return numero

    def clean(self):
        cleaned_data = super().clean()
        tipo_afiliacion = cleaned_data.get('tipo_afiliacion')
        nombre_eps = cleaned_data.get('nombre_eps')
        if tipo_afiliacion == Paciente.TipoAfiliacion.EPS and not nombre_eps:
            self.add_error('nombre_eps', 'Debes indicar el nombre de la EPS del paciente.')
        return cleaned_data


class PacienteEditForm(forms.ModelForm):
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
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }
