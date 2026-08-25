"""Dos rutas nada más: la página con el editor, y el endpoint que la
página llama para ejecutar el código. El "endpoint POST más pequeño
posible" del que habla el plan de la sesión.
"""

from django.urls import path

from interprete import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/interpretar', views.interpretar, name='interpretar'),
]
