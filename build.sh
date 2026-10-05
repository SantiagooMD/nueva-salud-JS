#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Crear o corregir usuarios del sistema
python manage.py shell -c "
from usuarios.models import Usuario

# Administrador
if not Usuario.objects.filter(username='admin').exists():
    u = Usuario.objects.create_superuser(
        username='admin',
        email='admin@nuevasalud.com',
        password='Admin12345',
        first_name='Admin',
        last_name='Sistema',
    )
    u.rol = 'ADMIN'
    u.save()
    print('Admin creado')
else:
    u = Usuario.objects.get(username='admin')
    u.rol = 'ADMIN'
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('Admin actualizado a rol ADMIN')

# Médico
if not Usuario.objects.filter(username='medico').exists():
    u = Usuario.objects.create_user(
        username='medico',
        email='medico@nuevasalud.com',
        password='medico123',
        first_name='Carlos',
        last_name='Ramirez',
    )
    u.rol = 'MEDICO'
    u.registro_medico = 'RM-12345'
    u.especialidad = 'Medicina General'
    u.save()
    print('Medico creado')
else:
    u = Usuario.objects.get(username='medico')
    u.rol = 'MEDICO'
    u.save()
    print('Medico actualizado a rol MEDICO')

# Recepcionista
if not Usuario.objects.filter(username='recepcion').exists():
    u = Usuario.objects.create_user(
        username='recepcion',
        email='recepcion@nuevasalud.com',
        password='recepcion123',
        first_name='Laura',
        last_name='Gomez',
    )
    u.rol = 'RECEPCIONISTA'
    u.save()
    print('Recepcionista creada')
else:
    u = Usuario.objects.get(username='recepcion')
    u.rol = 'RECEPCIONISTA'
    u.save()
    print('Recepcionista actualizada a rol RECEPCIONISTA')
"