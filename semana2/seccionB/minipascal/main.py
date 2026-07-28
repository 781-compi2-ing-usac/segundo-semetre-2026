"""
MiniPascal v1 — Punto de entrada.

Uso:
    python main.py                          (usa ejemplos/01_hola.mpas)
    python main.py ejemplos/02_aritmetica.mpas
    python main.py mi_programa.mpas

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

    # Ojo: si arriba salieron mensajes de error léxico, aquí igual dice
    # "AST construido". v1 IMPRIME los errores en el momento pero no los
    # GUARDA en ningún lado, así que nadie puede preguntar después "¿hubo
    # errores?". Recolectarlos en una lista es justo lo que agrega la
    # Sesión 2, y es también lo que necesitan para el reporte de errores
    # que pide el enunciado.
    print("AST construido.")

    # --- Paso 3: ejecución ------------------------------------------------
    print("\n=== SALIDA DEL PROGRAMA ===")
    try:
        # El `None` es el entorno. Todavía no existe (v1 no tiene variables),
        # pero el parámetro ya viaja por todo el AST para que en la Sesión 2
        # solo haya que cambiar este `None` por un `Entorno()`.
        arbol.ejecutar(None)
    except Exception as error:
        # Una operación inválida (`'hola' - 1`, dividir entre cero...) revienta
        # como error de Python, porque v1 todavía no valida tipos.
        # En la Sesión 2 esto se convierte en un error semántico con su línea
        # y columna, y la ejecución continúa en lugar de detenerse.
        print(f"\n[El intérprete se detuvo] {type(error).__name__}: {error}")
        print("(v1 no valida tipos todavía — eso es la Sesión 2)")

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
