"""
MiniPascal v3 — Punto de entrada.

Uso:
    python3 main.py                          (usa ejemplos/01_hola.mpas)
    python3 main.py ejemplos/02_aritmetica.mpas
    python3 main.py mi_programa.mpas

Este archivo muestra el flujo completo del intérprete, que es exactamente
el mismo que va a tener su proyecto:

    texto  ->  [lexer]  ->  tokens  ->  [parser]  ->  AST  ->  [ejecutar]

Fíjense en que son tres pasos SEPARADOS. Cuando algo falle van a poder
preguntarse "¿en cuál de los tres?" y revisar solo ese.
"""

import sys
import os

from parser import parsear
from dot import generar_dot, renderizar_png
from entorno import Entorno
from errores import ListaErrores
from tabla_simbolos import TablaSimbolos


def main():
    # Si no pasan archivo, usamos el ejemplo 1. La ruta se arma relativa a
    # este archivo para que funcione desde cualquier carpeta.
    aqui = os.path.dirname(os.path.abspath(__file__))
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(aqui, 'ejemplos', '01_hola.mpas')

    with open(ruta, encoding='utf-8') as archivo:
        codigo = archivo.read()

    print(f"=== ARCHIVO: {ruta} ===")
    print(codigo)

    # --- Paso 1 y 2: análisis léxico y sintáctico -------------------------
    print("=== ANÁLISIS ===")
    arbol = parsear(codigo)

    if arbol is None:
        print("No se pudo construir el AST. Se detiene aquí.")
        return 1

    # Ojo: si arriba salieron mensajes de error léxico o sintáctico, aquí
    # igual dice "AST construido". Esos dos SIGUEN sin acumularse en
    # ningún lado (solo se imprimen al vuelo) — la recuperación de
    # errores léxicos/sintácticos sigue pendiente, tal como decía el
    # comentario "LO QUE FALTA AQUÍ" de `p_error` en parser.py. Lo que sí
    # cambia esta semana son los errores SEMÁNTICOS: esos si se acumulan,
    # en `errores`, y no detienen la ejecución.
    print("AST construido.")

    # --- Paso 3: ejecución ------------------------------------------------
    entorno = Entorno()
    errores = ListaErrores()
    tabla = TablaSimbolos()

    print("\n=== SALIDA DEL PROGRAMA ===")
    try:
        arbol.ejecutar(entorno, errores, tabla)
    except Exception as error:
        # Una operación todavía sin tabla de tipos (`-`, `*`, `/` — solo
        # `+` está protegido, vean ast_nodes.Aritmetica) puede seguir
        # reventando como error de Python. Esto es exactamente el hueco
        # que se documenta ahí mismo: repliquen el patrón de `+` para
        # blindar los demás operadores.
        print(f"\n[El intérprete se detuvo] {type(error).__name__}: {error}")
        print("('-', '*', '/' todavía no tienen tabla de tipos — repítanla de '+'")

    print("\n=== ERRORES SEMÁNTICOS ===")
    errores.imprimir()

    print("\n=== TABLA DE SÍMBOLOS ===")
    tabla.imprimir()

    # --- Extra: el AST en formato Graphviz --------------------------------
    texto_dot = generar_dot(arbol)

    salida_dot = 'ast.dot'
    with open(salida_dot, 'w', encoding='utf-8') as archivo:
        archivo.write(texto_dot)

    print("\n=== AST ===")
    print(f"Texto DOT escrito en: {os.path.abspath(salida_dot)}")

    # `renderizar_png` necesita el programa `dot` instalado en el sistema
    # (no basta con el paquete de Python `graphviz`, que solo lo invoca).
    # Si no está, seguimos sin reventar: ya tienen el .dot para verlo en
    # línea, y el resto del intérprete no depende de esto para funcionar.
    salida_png = renderizar_png(texto_dot, 'ast.png')
    if salida_png:
        print(f"PNG renderizado en:  {os.path.abspath(salida_png)}")
    else:
        print("No se encontró el programa 'dot' del sistema "
              "(instálenlo con: sudo apt install graphviz).")
        print("Mientras tanto, peguen el contenido de ast.dot en "
              "https://dreampuf.github.io/GraphvizOnline/")

    return 0


if __name__ == '__main__':
    sys.exit(main())
