"""
MiniPascal v1 — Generación del AST en formato DOT (Graphviz).

El enunciado del proyecto pide un reporte gráfico del AST. Se los ponemos
desde la primera sesión no porque haya que entregarlo ya, sino porque es la
MEJOR herramienta de depuración que van a tener: cuando el intérprete dé un
resultado raro, casi siempre es porque el árbol no tiene la forma que creían.

La idea es corta: recorrer el árbol y escribir dos tipos de línea.

    n0 [label="Aritmetica +"];     <- un nodo
    n0 -> n1;                      <- una arista de padre a hijo

Este archivo no conoce ninguna clase del AST por nombre: usa `__dict__` para
descubrir los atributos de cada nodo. Por eso va a seguir funcionando en las
próximas semanas, cuando agreguemos nodos nuevos, sin tocarlo.
"""

import graphviz

from ast_nodes import Nodo, formatear


# Atributos que todos los nodos tienen pero que no aportan nada al dibujo.
IGNORADOS = {'linea', 'columna'}


def generar_dot(raiz):
    """Devuelve el texto DOT del árbol que cuelga de `raiz`."""
    lineas = [
        'digraph AST {',
        '  node [shape=box, fontname="Courier New"];',
    ]
    contador = [0]   # lista de un elemento: truco para poder mutarlo dentro
                     # de la función anidada sin usar `global`

    def recorrer(nodo):
        """Escribe `nodo` y sus hijos. Devuelve el id que le tocó."""
        mio = f'n{contador[0]}'
        contador[0] += 1

        etiquetas = []
        hijos = []

        # Separamos los atributos en dos grupos:
        #   - los que son otros nodos (o listas de nodos) -> son hijos
        #   - los que son valores sueltos                 -> van en la etiqueta
        for nombre, valor in vars(nodo).items():
            if nombre in IGNORADOS:
                continue
            if isinstance(valor, Nodo):
                hijos.append((nombre, valor))
            elif isinstance(valor, list):
                for elemento in valor:
                    if isinstance(elemento, Nodo):
                        hijos.append((nombre, elemento))
            else:
                # `formatear` en vez de `str` para que un booleano se dibuje
                # como `true` y no como el `True` de Python: el dibujo debe
                # hablar en el lenguaje que estamos implementando.
                etiquetas.append(formatear(valor))

        # `\n` dentro de un label de DOT es un salto de línea en el dibujo.
        # Se escribe DESPUÉS de escapar, porque si no el propio escape se lo
        # comería convirtiéndolo en una barra literal.
        titulo = escapar(type(nodo).__name__)
        if etiquetas:
            titulo += '\\n' + escapar(' '.join(etiquetas))

        lineas.append(f'  {mio} [label="{titulo}"];')

        for nombre, hijo in hijos:
            suyo = recorrer(hijo)
            lineas.append(f'  {mio} -> {suyo} [label="{nombre}"];')

        return mio

    recorrer(raiz)
    lineas.append('}')
    return '\n'.join(lineas)


def escapar(texto):
    """Las comillas y las barras rompen la sintaxis de DOT; hay que escaparlas.

    Prueben `writeln('dijo ''hola''');` sin esta función y verán que el
    archivo .dot generado ya no se puede abrir.
    """
    return texto.replace('\\', '\\\\').replace('"', '\\"')


def renderizar_png(texto_dot, ruta_salida='ast.png'):
    """Convierte el texto DOT directamente a una imagen PNG.

    OJO con la diferencia entre dos cosas que se llaman parecido:

      - el paquete de Python `graphviz` (el que importamos arriba) es solo
        un MENSAJERO: arma el texto y se lo entrega al programa `dot`.
      - el programa `dot` es el que realmente dibuja. Es software en C,
        instalado por el sistema operativo (`sudo apt install graphviz`),
        no algo que pip pueda instalar.

    Por eso, aunque `pip install graphviz` haya funcionado, esta función
    puede fallar en una máquina donde no se instaló el paquete del sistema.
    Devolvemos None en ese caso en vez de reventar, para que main.py pueda
    seguir funcionando con el archivo .dot solo (que sí generamos siempre).

    Esto es exactamente el patrón que van a necesitar en su proyecto: el
    reporte de AST no puede tumbar el resto del intérprete si Graphviz no
    está disponible en la máquina donde corre.
    """
    grafo = graphviz.Source(texto_dot)
    try:
        return grafo.render(outfile=ruta_salida, cleanup=True)
    except graphviz.ExecutableNotFound:
        return None


if __name__ == '__main__':
    # Correr "python dot.py" imprime el DOT de un árbol de ejemplo.
    from parser import parsear

    arbol = parsear("""program Demo;
begin
  writeln(2 + 3 * 4);
end.
""")
    texto = generar_dot(arbol)
    print(texto)

    ruta = renderizar_png(texto, 'ast.png')
    if ruta:
        print(f"\nPNG generado en: {ruta}")
    else:
        print("\nNo se encontró el programa 'dot' del sistema "
              "(sudo apt install graphviz). Peguen el texto de arriba en "
              "https://dreampuf.github.io/GraphvizOnline/ mientras tanto.")
