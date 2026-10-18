from django.db import migrations

from catalogos.datos_iniciales import ENFERMEDADES, MEDICAMENTOS


def cargar_catalogos(apps, schema_editor):
    """
    Carga los catálogos de partida. Es idempotente: si el administrador ya agregó una enfermedad o
    un medicamento con el mismo nombre, no se duplica ni se modifica.
    """
    Enfermedad = apps.get_model('catalogos', 'Enfermedad')
    Medicamento = apps.get_model('catalogos', 'Medicamento')

    for codigo, nombre in ENFERMEDADES:
        Enfermedad.objects.get_or_create(nombre=nombre, defaults={'codigo': codigo, 'activo': True})

    for nombre, presentacion in MEDICAMENTOS:
        Medicamento.objects.get_or_create(
            nombre=nombre, defaults={'presentacion': presentacion, 'activo': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0001_initial'),
    ]

    operations = [
        # Al revertir no se borra nada: podrían estar referenciados por consultas existentes.
        migrations.RunPython(cargar_catalogos, migrations.RunPython.noop),
    ]
