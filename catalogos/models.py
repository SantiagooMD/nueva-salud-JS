from django.db import models


class Enfermedad(models.Model):
    """Catálogo de enfermedades / diagnósticos (selección, no texto libre)."""
    codigo = models.CharField(max_length=20, blank=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Enfermedad'
        verbose_name_plural = 'Enfermedades'
        ordering = ['nombre']

    def __str__(self):
        if self.codigo:
            return f'{self.codigo} - {self.nombre}'
        return self.nombre


class Medicamento(models.Model):
    """Catálogo de medicamentos (selección, no texto libre)."""
    nombre = models.CharField(max_length=200, unique=True)
    presentacion = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering = ['nombre']

    def __str__(self):
        if self.presentacion:
            return f'{self.nombre} ({self.presentacion})'
        return self.nombre


