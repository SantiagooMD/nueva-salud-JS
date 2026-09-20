from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuario del sistema Nueva Salud JS.
    Roles: Administrador, Médico, Recepcionista
    """

    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', 'Administrador'
        MEDICO = 'MEDICO', 'Médico'
        RECEPCIONISTA = 'RECEPCIONISTA', 'Recepcionista'

    # Campos extra que necesitamos
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.RECEPCIONISTA,
        verbose_name='Rol'
    )
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    
    # Campos que se usarán después para médicos (Sprint 3)
    registro_medico = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name='Número de registro médico'
    )
    especialidad = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Especialidad'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    # Métodos útiles para saber el rol
    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_medico(self):
        return self.rol == self.Rol.MEDICO

    @property
    def es_recepcionista(self):
        return self.rol == self.Rol.RECEPCIONISTA