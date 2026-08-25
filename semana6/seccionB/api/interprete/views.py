"""
El endpoint. Todo lo que hace es: recibir código MiniPascal, correrlo con
el MISMO intérprete que ya usan desde `main.py`, y devolver el resultado
como JSON — sin duplicar ni una línea de lexer/parser/ast_nodes.

*** LA ADVERTENCIA MÁS IMPORTANTE DE ESTA SESIÓN ***

Un servidor web atiende MUCHAS peticiones, una tras otra (o al mismo
tiempo). Si `entorno`, `errores` o `tabla` fueran variables de MÓDULO
(creadas una sola vez, arriba de este archivo, fuera de la función) en
vez de crearse DE NUEVO en cada llamada a `interpretar`, las variables de
un programa se mezclarían con las del programa anterior — o con las de
OTRO usuario corriendo su propio código al mismo tiempo. Por eso las tres
se crean adentro de la función, en cada petición.
"""

import contextlib
import io
import json
import os
import sys

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# minipascal/ vive fuera de este proyecto de Django (es una carpeta
# hermana de api/, no algo instalado como paquete). Lo agregamos al
# `sys.path` para poder importarlo tal cual, sin copiar ni un archivo.
AQUI = os.path.dirname(os.path.abspath(__file__))
MINIPASCAL_DIR = os.path.normpath(os.path.join(AQUI, '..', '..', 'minipascal'))
if MINIPASCAL_DIR not in sys.path:
    sys.path.insert(0, MINIPASCAL_DIR)

from parser import parsear           # noqa: E402 (import después del sys.path a propósito)
from entorno import Entorno          # noqa: E402
from errores import ListaErrores     # noqa: E402
from tabla_simbolos import TablaSimbolos   # noqa: E402


def index(request):
    """La página con el textarea y el botón. Nada más."""
    return render(request, 'interprete/index.html')


@csrf_exempt   # ver "Qué falta para tu proyecto" — esto es SOLO para este demo
@require_http_methods(['POST'])
def interpretar(request):
    datos = json.loads(request.body)
    codigo = datos.get('codigo', '')

    entorno = Entorno()
    errores = ListaErrores()
    tabla = TablaSimbolos()

    arbol = parsear(codigo)

    # `Writeln.ejecutar` (en ast_nodes.py) llama `print(...)` — eso
    # escribe en la consola del SERVIDOR, no en algo que le podamos
    # devolver al navegador. `redirect_stdout` intercepta esas llamadas a
    # `print()` y las junta en un buffer, SIN tocar una sola línea de
    # ast_nodes.py. Así es como capturan la "consola de salida" que pide
    # la sección 3.1.2 del enunciado.
    buffer_salida = io.StringIO()

    if arbol is not None:
        with contextlib.redirect_stdout(buffer_salida):
            try:
                arbol.ejecutar(entorno, errores, tabla)
            except Exception as error:
                # Una operación sin tabla de tipos todavía (ver
                # ast_nodes.Aritmetica) puede reventar como excepción de
                # Python. Sin este `except`, ESA excepción tumbaría el
                # proceso de Django completo — no solo esta petición, el
                # servidor entero. Un endpoint SIEMPRE debe devolver una
                # respuesta, nunca dejar que una excepción se escape.
                errores.agregar('Semántico', f'{type(error).__name__}: {error}', 0, 0)

    return JsonResponse({
        'salida': buffer_salida.getvalue(),
        'errores': errores.errores,
        'simbolos': tabla.filas,
    })
