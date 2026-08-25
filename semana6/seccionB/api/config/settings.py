"""
Configuración de Django, recortada a lo mínimo para este ejemplo.

Comparen con lo que genera 'django-admin startproject': ahí vienen
'django.contrib.admin/auth/sessions/messages' en INSTALLED_APPS, que
necesitan una base de datos (hay que correr 'manage.py migrate' antes de
poder arrancar). Aquí NO los incluimos a propósito — este ejemplo no
necesita guardar nada en una base de datos, así que `runserver` funciona
de una vez, sin pasos previos. Su proyecto real sí va a necesitar algunas
de esas apps si guardan usuarios o sesiones.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Ojo: esto es SOLO para correr localmente en su máquina, durante la
# clase. Una SECRET_KEY así, en texto plano en el repositorio, NUNCA debe
# usarse en un proyecto que de verdad se vaya a desplegar.
SECRET_KEY = 'solo-para-este-ejemplo-de-clase'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'interprete',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [],
        },
    },
]

USE_TZ = True
