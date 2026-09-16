"""
MiniPascal v6 — La interfaz Visitante.

Un visitante es un objeto con un método por cada tipo de nodo del AST.
Nada más. Esta clase base los declara todos y les da un comportamiento
por defecto útil: quejarse con un mensaje claro.

Por qué eso importa: `interprete.py` implementa los 30 métodos, pero
`generador_arm.py` implementa solo unos pocos (hoy: literales enteros,
aritmética y `writeln`). Cuando el generador se tope con un nodo que
todavía no sabe traducir, no van a recibir un `AttributeError` críptico
sino:

    [generador] Todavía no sé generar ensamblador para: While (línea 7).

Ese mensaje es el mapa de lo que falta. Al ir creciendo el generador
sesión por sesión, van a ver la lista encogerse.


Cómo se usa
-----------
    class MiVisitante(Visitante):
        def visitar_Literal(self, nodo):
            return nodo.valor

    resultado = arbol.aceptar(MiVisitante())


Un detalle que se les va a hacer raro al principio
--------------------------------------------------
Los métodos reciben SOLO el nodo. ¿Dónde quedó el `entorno` que antes se
pasaba de mano en mano (`evaluar(entorno, errores, tabla)`)?

Pasó a ser estado DEL VISITANTE: `self.entorno`, `self.errores`,
`self.tabla`. Es lo que hace que la firma sea uniforme —todos los
métodos se ven igual—, y es obligatorio para que el patrón sirva: cada
visitante necesita un estado distinto. El intérprete necesita un entorno
de valores; el generador necesita un contador de etiquetas y el texto del
ensamblador que lleva escrito. No hay una firma común que sirva para los
dos.

La regla que se llevan:

    el árbol no recuerda nada  ->  el visitante recuerda todo
"""


NOMBRES_DE_NODOS = [
    # Expresiones
    'Literal', 'Variable', 'Aritmetica', 'Negacion', 'Comparacion',
    'Llamada', 'Slice', 'Indexado', 'AccesoCampo',
    # Instrucciones
    'Writeln', 'Declaracion', 'DeclaracionInferida', 'DeclaracionArreglo',
    'Asignacion', 'AsignacionIndexada', 'AsignacionCampo', 'Bloque',
    'If', 'While', 'Repeat', 'Case', 'RamaCase', 'Break', 'Continue',
    'Funcion', 'Parametro', 'Return', 'TipoRegistro', 'DeclaracionRegistro',
    # Raíz
    'Programa',
]


class Visitante:
    """Clase base. Hereden de aquí y sobrescriban lo que necesiten."""

    # Nombre que aparece en el mensaje de error. Cada visitante concreto
    # lo cambia por el suyo.
    etiqueta = 'visitante'

    def no_implementado(self, nodo):
        raise NotImplementedError(
            f"[{self.etiqueta}] Todavía no sé qué hacer con: "
            f"{type(nodo).__name__} (línea {nodo.linea})."
        )


# Los 30 métodos `visitar_X` por defecto se crean aquí, en un bucle, en vez
# de escribirlos treinta veces a mano. No es magia: es exactamente lo mismo
# que haber escrito
#
#     def visitar_Literal(self, nodo):
#         return self.no_implementado(nodo)
#
# una vez por cada nombre de la lista. Si prefieren verlos escritos —y
# para su proyecto quizá convenga, porque el autocompletado del editor los
# encuentra— escríbanlos; el patrón es idéntico.
def _crear_metodo_por_defecto(nombre):
    def metodo(self, nodo):
        return self.no_implementado(nodo)
    metodo.__name__ = f'visitar_{nombre}'
    return metodo


for _nombre in NOMBRES_DE_NODOS:
    setattr(Visitante, f'visitar_{_nombre}', _crear_metodo_por_defecto(_nombre))
del _nombre
