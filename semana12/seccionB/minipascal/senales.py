"""
MiniPascal v4 — Señales de control de flujo.

Ver micro/01_senales.py (Sesión 3) para la explicación completa de por qué
esto se hace con excepciones y no con banderas, y
micro/02_limite_de_funcion.py (esta semana) para el porqué de que
`SenalReturn` la atrape específicamente la llamada a función, y de nadie
más — ni siquiera un `while` que esté de por medio.
"""


class SenalBreak(Exception):
    """`break;` o `break etiqueta;`."""

    def __init__(self, etiqueta, linea, columna):
        self.etiqueta = etiqueta   # None = "el ciclo más cercano"
        self.linea = linea
        self.columna = columna


class SenalContinue(Exception):
    """`continue;` o `continue etiqueta;`. Misma idea que SenalBreak."""

    def __init__(self, etiqueta, linea, columna):
        self.etiqueta = etiqueta
        self.linea = linea
        self.columna = columna


class SenalReturn(Exception):
    """`return expresion;`

    A diferencia de SenalBreak/SenalContinue, no lleva etiqueta: un
    `return` siempre pertenece a la llamada de función más cercana que lo
    contiene, sin excepción — MiniPascal no tiene funciones anidadas
    dentro de otras funciones, así que nunca hay ambigüedad sobre a cuál
    llamada le toca atraparla.
    """

    def __init__(self, valor, linea, columna):
        self.valor = valor
        self.linea = linea
        self.columna = columna
