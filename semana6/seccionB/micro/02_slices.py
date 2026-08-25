"""
MICRO-EJEMPLO 2: Slices — una VISTA, no una copia. Sin PLY.

Objetivo: entender la diferencia entre "copiar" y "ver" un arreglo, y por
qué un slice tiene que ser lo segundo.

Repaso rápido de la Sesión 4: cuando pasan un arreglo a una función, se
COPIA (`list(arreglo)`) — así, lo que la función le hace a su copia no se
ve afuera. Eso es correcto para arreglos.

Un slice es distinto A PROPÓSITO. El enunciado lo dice explícito: "a
diferencia de un arreglo, un slice no almacena los datos, sino que hace
referencia a una parte de un arreglo existente" — sin copiar. Si
`slice[0] := 99` cambia el arreglo original, es porque el slice nunca
tuvo sus propios datos: solo apunta a una porción del original.

En Python, `lista[1:4]` NO sirve para esto — eso SÍ copia. Hay que
construir la vista a mano.

Correr con: python 02_slices.py
"""


class VistaArreglo:
    """Una vista sobre parte de un arreglo, SIN copiar sus datos.

    Guarda una referencia al arreglo ORIGINAL (el mismo objeto de
    Python, no una copia) más un rango [inicio, fin). Leer o escribir a
    través de la vista lee o escribe directamente sobre el arreglo
    original.
    """

    def __init__(self, arreglo_original, inicio, fin):
        self.arreglo_original = arreglo_original
        self.inicio = inicio
        self.fin = fin   # no incluido, como en el enunciado: [inicio, fin)

    def __len__(self):
        return self.fin - self.inicio

    def __getitem__(self, indice_local):
        # Sin este chequeo, iterar la vista con el protocolo "viejo" de
        # Python (el que se usa cuando no hay __iter__) seguiría de largo
        # más allá de `self.fin`, hacia el arreglo ORIGINAL completo, en
        # vez de detenerse en el borde del slice.
        if not (0 <= indice_local < len(self)):
            raise IndexError(indice_local)
        return self.arreglo_original[self.inicio + indice_local]

    def __setitem__(self, indice_local, valor):
        if not (0 <= indice_local < len(self)):
            raise IndexError(indice_local)
        self.arreglo_original[self.inicio + indice_local] = valor

    def __repr__(self):
        # Para que se imprima como una lista normal, aunque por dentro
        # sea otra cosa completamente distinta.
        elementos = ', '.join(str(self[i]) for i in range(len(self)))
        return f'[{elementos}]'


if __name__ == '__main__':
    numeros = [10, 20, 30, 40, 50]
    print(f"Arreglo original: {numeros}")

    # &numeros[1..4]  ->  VistaArreglo(numeros, 1, 4)
    parte = VistaArreglo(numeros, 1, 4)
    print(f"Slice numeros[1..4]: {parte}")   # [20, 30, 40]

    print("\n¿Por qué __len__/__getitem__/__setitem__ y no otra cosa?")
    print("Porque así Python deja usar `len(parte)`, `parte[i]` y")
    print("`parte[i] = valor` con la MISMA sintaxis que una lista normal,")
    print("sin que el resto del código tenga que saber que por dentro es")
    print("una vista y no una lista de verdad. Pruébenlo:")
    print(f"  len(parte)  = {len(parte)}")
    print(f"  parte[0]    = {parte[0]}")

    print("\nModificar A TRAVÉS del slice cambia el arreglo original:")
    parte[0] = 99
    print(f"  parte           = {parte}")
    print(f"  numeros_original = {numeros}")
    print("  (numeros[1] ahora es 99 — el slice NUNCA tuvo sus propios")
    print("   datos, solo apuntaba a una porción de numeros)")

    print("\nY al revés: modificar el arreglo original se ve en el slice:")
    numeros[2] = 777
    print(f"  numeros = {numeros}")
    print(f"  parte   = {parte}")
    print("  (parte[1] corresponde a numeros[2] — cambió solo)")

    print("\nComparen con lo que pasaría con un arreglo COPIADO (Sesión 4):")
    copia = list(numeros[1:4])   # esto SÍ copia — el slicing normal de Python
    copia[0] = -1
    print(f"  copia   = {copia}")
    print(f"  numeros = {numeros}")
    print("  (numeros NO cambió: 'copia' es una lista nueva e independiente,")
    print("   exactamente lo que NO queremos para un slice)")

    # ---------------------------------------------------------------
    # Para su proyecto:
    #
    # - `Indexado`/`AsignacionIndexada` de la Sesión 4 ya usan
    #   `arreglo[indice]` y `len(arreglo)` — si `VistaArreglo` responde a
    #   esos mismos dos protocolos, esas clases casi no necesitan cambiar
    #   para aceptar un slice además de un arreglo normal. Revisen
    #   `Indexado.evaluar` en `ast_nodes.py` y busquen qué línea cambió.
    # - Cuando un slice se pasa como argumento a una función, NO debe
    #   copiarse (a diferencia de un arreglo) — pasar la MISMA
    #   `VistaArreglo` (o una copia superficial del envoltorio, que sigue
    #   apuntando al mismo arreglo original) preserva el comportamiento
    #   de "vista, no copia" también a través de una llamada.
    # ---------------------------------------------------------------
