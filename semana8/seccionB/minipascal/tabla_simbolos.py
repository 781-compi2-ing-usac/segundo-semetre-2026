"""
MiniPascal v2 — Tabla de símbolos.

*** NO confundir con `Entorno` (entorno.py). Son cosas distintas. ***

  - `Entorno` vive en TIEMPO DE EJECUCIÓN, tiene forma de árbol (cada
    bloque el suyo, con padre), y cuando un bloque termina su Entorno se
    descarta — las variables locales dejan de existir.

  - `TablaSimbolos` es UNA SOLA, para todo el programa, de principio a
    fin. Nunca se descarta nada: es una bitácora que solo CRECE, pensada
    para generar el reporte que pide el enunciado (sección 3.4.2), no para
    que el intérprete busque valores ahí.

Por eso cada `Declaracion.ejecutar` hace DOS cosas con dos objetos
distintos: `entorno.declarar(...)` (para poder usar la variable mientras
el programa corre) Y `tabla.registrar(...)` (para que quede constancia,
aunque esa variable ya haya salido de ámbito cuando el programa termine).

OJO con un detalle: el "Valor" que se registra aquí es el que tenía la
variable EN EL MOMENTO DE DECLARARLA, no su valor final. Si después el
programa hace `edad := edad + 1;`, esa fila de la tabla NO se actualiza —
solo `Entorno` se entera del cambio. Es una decisión de diseño (la tabla
es una bitácora de "qué se declaró", no una foto en vivo del `Entorno`),
no un descuido. Si su proyecto necesita el valor final, van a tener que
decidir cuándo tomar esa foto.
"""


class TablaSimbolos:

    def __init__(self):
        self.filas = []

    def registrar(self, nombre, categoria, tipo, ambito, linea, valor):
        """`categoria` es 'Variable' o 'Constante'. `ambito` es el nombre
        del alcance donde se declaró ('programa' por ahora; en la Sesión 4,
        cuando existan funciones, aquí va a aparecer el nombre de la
        función)."""
        self.filas.append({
            'nombre': nombre,
            'categoria': categoria,
            'tipo': tipo,
            'ambito': ambito,
            'linea': linea,
            'valor': valor,
        })

    def imprimir(self):
        if not self.filas:
            print("(tabla de símbolos vacía)")
            return

        encabezado = f"{'#':>3} {'Identificador':<15} {'Categoría':<10} {'Tipo':<10} {'Ámbito':<10} {'Línea':>6} {'Valor'}"
        print(encabezado)
        print('-' * len(encabezado))
        for numero, fila in enumerate(self.filas, start=1):
            print(f"{numero:>3} {fila['nombre']:<15} {fila['categoria']:<10} "
                  f"{fila['tipo']:<10} {fila['ambito']:<10} {fila['linea']:>6} "
                  f"{fila['valor']}")


if __name__ == '__main__':
    tabla = TablaSimbolos()
    tabla.registrar('contador', 'Variable', 'integer', 'programa', 1, 10)
    tabla.registrar('PI', 'Constante', 'real', 'programa', 2, 3.14)
    tabla.imprimir()

    # ---------------------------------------------------------------
    # Para su proyecto: esta tabla, junto con `ListaErrores`, es la
    # materia prima de dos de los tres reportes que pide el enunciado
    # (sección 3.4). El tercero es el AST, que ya tienen desde la
    # Sesión 1 con `dot.py`. Convertir estas filas a HTML es solo
    # cuestión de un f-string con etiquetas <table><tr><td> alrededor de
    # este mismo `imprimir()`.
    # ---------------------------------------------------------------
