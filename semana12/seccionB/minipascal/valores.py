"""
MiniPascal v6 — VALORES en tiempo de ejecución.

Este archivo es nuevo, y la razón de que exista es la idea más importante
del Proyecto 2. Hasta la Sesión 5 todo vivía junto en `ast_nodes.py`: los
nodos del árbol y los valores que esos nodos producían. Ahora los
separamos, porque son cosas de DOS MOMENTOS distintos:

    ast_nodes.py  ->  lo que existe en tiempo de COMPILACIÓN
                      (la forma del programa: nodos, hijos, línea y columna)

    valores.py    ->  lo que existe en tiempo de EJECUCIÓN
                      (enteros, cadenas, arreglos, registros, vistas)

Un intérprete mezcla los dos momentos: recorre el árbol Y produce valores,
todo al mismo tiempo. Un compilador NO. Cuando ustedes generen ensamblador,
el programa todavía no se ha ejecutado: no hay ningún valor en ningún lado,
solo la forma. Por eso `generador_arm.py` no importa nada de este archivo,
y `interprete.py` sí importa todo.

Si esa distinción les queda clara hoy, se ahorran la confusión más común
del Proyecto 2: intentar "calcular" cosas mientras generan código.
"""


VALORES_POR_DEFECTO = {
    'integer': 0,
    'real': 0.0,
    'boolean': False,
    'string': '',
}


def tipo_de_valor(valor):
    """Deriva el tipo de MiniPascal a partir de un valor de Python.

    Un arreglo (lista de Python) no tiene un tipo MiniPascal representable
    aquí con esta función de una sola palabra — por eso el intérprete
    comprueba `isinstance(..., list)` directamente en vez de pasar por
    `tipo_de_valor`.
    """
    if isinstance(valor, bool):
        return 'boolean'
    if isinstance(valor, int):
        return 'integer'
    if isinstance(valor, float):
        return 'real'
    if isinstance(valor, str):
        return 'string'
    return None


class VistaArreglo:
    """Una vista sobre parte de un arreglo, SIN copiar sus datos.

    NO es un `Nodo` — nunca aparece en el AST. Es un VALOR en tiempo de
    ejecución, exactamente como una `list` de Python lo es para un
    arreglo normal. Por eso vive aquí y no en `ast_nodes.py`. Ver
    semana6/seccionB/micro/02_slices.py para la explicación completa.
    """

    def __init__(self, arreglo_original, inicio, fin):
        self.arreglo_original = arreglo_original
        self.inicio = inicio
        self.fin = fin   # no incluido: [inicio, fin)

    def __len__(self):
        return self.fin - self.inicio

    def __getitem__(self, indice_local):
        if not (0 <= indice_local < len(self)):
            raise IndexError(indice_local)
        return self.arreglo_original[self.inicio + indice_local]

    def __setitem__(self, indice_local, valor):
        if not (0 <= indice_local < len(self)):
            raise IndexError(indice_local)
        self.arreglo_original[self.inicio + indice_local] = valor

    def __repr__(self):
        return '[' + ', '.join(str(self[i]) for i in range(len(self))) + ']'


# El intérprete acepta un arreglo O una vista en los mismos lugares — de
# ahí este alias, para no repetir `(list, VistaArreglo)` en cada isinstance.
TIPOS_INDEXABLES = (list, VistaArreglo)


class FuncionValor:
    """Una función lista para llamarse: su declaración + el entorno donde
    fue declarada.

    Esto ANTES vivía dentro del nodo `Funcion`, en un atributo
    `entorno_definicion` que `ejecutar()` rellenaba. Al pasar a Visitor
    eso dejó de tener sentido: un nodo describe la FORMA del programa y
    debe poder recorrerse muchas veces, con visitantes distintos, sin
    guardarse nada de una pasada para la siguiente. Un nodo que recuerda
    algo de la última ejecución ya no es una descripción, es un estado.

    Así que el nodo `Funcion` volvió a ser solo datos, y el intérprete
    guarda ESTO en el entorno. Es la misma idea que un cierre (closure)
    de Python o JavaScript: la función más el entorno donde nació.
    """

    def __init__(self, declaracion, entorno_definicion):
        self.declaracion = declaracion             # el nodo Funcion
        self.entorno_definicion = entorno_definicion

    @property
    def parametros(self):
        return self.declaracion.parametros

    @property
    def tipo_retorno(self):
        return self.declaracion.tipo_retorno

    @property
    def cuerpo(self):
        return self.declaracion.cuerpo

    def __repr__(self):
        return f'<funcion {self.declaracion.nombre}>'


def describir_tipo(valor):
    """Como `tipo_de_valor`, pero también sabe describir arreglos,
    registros y slices — cosas que no tienen una sola palabra de tipo.
    Solo se usa para mostrar algo razonable en la tabla de símbolos.
    """
    tipo_simple = tipo_de_valor(valor)
    if tipo_simple is not None:
        return tipo_simple
    if isinstance(valor, list):
        if valor:
            return f'array[{len(valor)}] of {describir_tipo(valor[0])}'
        return 'array[0] of ?'
    if isinstance(valor, dict):
        return '<registro>'
    if isinstance(valor, VistaArreglo):
        return 'slice'
    if isinstance(valor, FuncionValor):
        return 'function'
    return '?'


def formatear(valor):
    """Convierte un valor de MiniPascal a texto para imprimirlo."""
    if isinstance(valor, bool):
        return 'true' if valor else 'false'
    if isinstance(valor, TIPOS_INDEXABLES):
        return '[' + ', '.join(formatear(valor[i]) for i in range(len(valor))) + ']'
    if isinstance(valor, dict):
        campos = ', '.join(f'{nombre}: {formatear(v)}' for nombre, v in valor.items())
        return '{' + campos + '}'
    return str(valor)
