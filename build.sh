#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Crear usuarios del sistema si no existen
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
    print('Admin ya existe')

# Médico
if not Usuario.objects.filter(username='medico').exists():
    u = Usuario.objects.create_user(
        username='medico',
        email='medico@nuevasalud.com',
        password='medico123',
        first_name='Carlos',
        last_name='Ramírez',
    )
    u.rol = 'MEDICO'
    u.registro_medico = 'RM-12345'
    u.especialidad = 'Medicina General'
    u.save()
    print('Medico creado')
else:
    print('Medico ya existe')

# Recepcionista
if not Usuario.objects.filter(username='recepcion').exists():
    u = Usuario.objects.create_user(
        username='recepcion',
        email='recepcion@nuevasalud.com',
        password='recepcion123',
        first_name='Laura',
        last_name='Gómez',
    )
    u.rol = 'RECEPCIONISTA'
    u.save()
    print('Recepcionista creada')
else:
    print('Recepcionista ya existe')
"