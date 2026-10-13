"""
MICRO-EJEMPLO 6: la pila de llamadas, un frame por llamada. Sin PLY.

En `arm/07_funciones.s`, cada llamada a `factorial` guarda su propio `n`
y su propia dirección de retorno en la pila. Aquí lo modelamos con una
lista de Python para VER cómo crece y cómo se vacía mientras corre:

    factorial(3)  ->  3 * factorial(2)
                      factorial(2)  ->  2 * factorial(1)
                                        factorial(1)  ->  1

La pila crece con cada `bl` y se deshace con cada `ret`, en orden
inverso. Eso es todo lo que es "recursión" para el procesador.

Correr con: python3 06_pila_de_llamadas.py
"""

pila = []        # cada elemento es un frame: lo que guardó UNA llamada


def mostrar(titulo):
    print(f"--- {titulo}")
    if not pila:
        print("    (pila vacía)")
    # Se imprime de arriba (la más reciente) hacia abajo (main)
    for frame in reversed(pila):
        print(f"    | {frame['funcion']}(n={frame['n']})   vuelve a: {frame['retorno']}")
    print()


def factorial(n, retorno):
    # PRÓLOGO: `stp x29, x30` y `sub sp` — el frame de ESTA llamada
    pila.append({'funcion': 'factorial', 'n': n, 'retorno': retorno})
    mostrar(f"entró factorial({n})")

    if n <= 1:
        resultado = 1
    else:
        # `bl factorial`: una llamada nueva, con un frame nuevo ENCIMA
        resultado = n * factorial(n - 1, retorno=f"factorial({n}), después del bl")

    # EPÍLOGO: `mov sp, x29` y `ldp` — el frame de ESTA llamada desaparece
    pila.pop()
    mostrar(f"salió factorial({n}) devolviendo {resultado}")
    return resultado


print("Programa:  writeln(factorial(3));\n")
valor = factorial(3, retorno="main, después del bl")
print(f"main imprime: {valor}")

print("""
Fíjense en tres cosas:

  1. Cada línea de la pila tiene SU PROPIO n. La n de factorial(3) sigue
     valiendo 3 mientras factorial(1) corre arriba de ella.

  2. La dirección de retorno es distinta en cada frame. Por eso hace
     falta guardar x30 en CADA prólogo: el `bl` de la llamada de adentro
     pisa x30, y si no se guardó, la de afuera ya no sabe dónde volver.

  3. La pila nunca tiene más frames que la profundidad de la recursión.
     Una recursión sin caso base (`factorial(n)` que nunca para) agota
     el stack: es el "Segmentation fault" que ya vieron con el ciclo de
     las variables, por otra razón.

Para pensar: ¿cuánto crece la pila (en bytes) por cada llamada de
`factorial` en `07_funciones.s`? Cuenten el `stp`, el `sub sp` y el
temporal que empuja el operando izquierdo de `n * ...`.
""")
