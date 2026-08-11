"""
MiniPascal v3 — Señales de control de flujo.

Ver micro/01_senales.py para la explicación completa de por qué esto se
hace con excepciones y no con banderas.

Solo `SenalBreak` y `SenalContinue` por ahora. `SenalReturn` se agrega en
la Sesión 4, cuando existan funciones — no tiene sentido antes, porque
nada la va a atrapar todavía.
"""


class SenalBreak(Exception):
    """`break;` o `break etiqueta;`.

    Guarda también línea y columna: si esta señal llega hasta
    `Programa.ejecutar` sin que ningún ciclo la haya atrapado (un `break`
    fuera de cualquier ciclo), ahí se reporta como error semántico, y hace
    falta la posición original para el mensaje.
    """

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
