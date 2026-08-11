"""
MICRO-EJEMPLO 1: Señales de control de flujo, sin PLY.

Objetivo: entender POR QUÉ `break`, `continue` y `return` se implementan
con EXCEPCIONES de Python en un intérprete recursivo, y no con una
variable tipo `detener = True` que hay que ir revisando manualmente en
cada nivel de la recursión.

El problema con una bandera: `break` puede ocurrir dentro de un `if`,
dentro de un bloque, dentro de un `while`, dentro de otro bloque más...
Con una bandera, CADA UNO de esos niveles tendría que revisar "¿me
dijeron que pare?" después de cada instrucción y cortar su propio `for`.
Se vuelve código repetido y frágil.

Con una excepción, ninguno de esos niveles intermedios necesita saber
nada: la excepción sube sola por la pila de llamadas hasta el primer que
sepa atraparla. Eso es exactamente lo que Python ya hace gratis.

Correr con: python3 01_senales.py
"""


class SenalBreak(Exception):
    """Se lanza cuando el programa MiniPascal ejecuta `break` (o
    `break 'etiqueta;`). `etiqueta=None` significa "el ciclo más cercano"."""

    def __init__(self, etiqueta=None):
        self.etiqueta = etiqueta


class SenalContinue(Exception):
    """Igual que SenalBreak, pero para `continue`."""

    def __init__(self, etiqueta=None):
        self.etiqueta = etiqueta


class SenalReturn(Exception):
    """Se lanza cuando el programa MiniPascal ejecuta `return valor;`."""

    def __init__(self, valor):
        self.valor = valor


def ejecutar_bloque(instrucciones):
    """Simula Bloque.ejecutar: corre una lista de instrucciones (aquí,
    funciones de Python sin argumentos) una tras otra."""
    for instruccion in instrucciones:
        instruccion()


def bucle_while(condicion, cuerpo, etiqueta=None):
    """Simula While.ejecutar: corre `cuerpo` mientras `condicion()` sea
    verdadera, atrapando las señales de Break/Continue que le correspondan
    a ESTE ciclo.
    """
    while condicion():
        try:
            ejecutar_bloque(cuerpo)
        except SenalContinue as señal:
            if señal.etiqueta not in (None, etiqueta):
                raise   # no era para mí: que la siga atrapando alguien más arriba
            continue
        except SenalBreak as señal:
            if señal.etiqueta not in (None, etiqueta):
                raise
            break
        # OJO: SenalReturn NO se atrapa aquí. Un ciclo nunca debe
        # "absorber" un return — tiene que seguir subiendo hasta la
        # llamada de función que lo originó, aunque tenga que atravesar
        # varios ciclos anidados en el camino. Por eso no hay
        # `except SenalReturn` en este `try`: al no atraparla, Python la
        # deja pasar de largo sola.


if __name__ == '__main__':
    # -----------------------------------------------------------------
    # Demo 1: break sencillo, sin etiqueta
    # -----------------------------------------------------------------
    print("Demo 1: break sencillo")
    contador = [0]   # lista de un elemento: el mismo truco de dot.py para
                      # poder mutar una variable "de afuera" desde una
                      # función anidada, sin usar `nonlocal`

    def cuerpo_1():
        contador[0] += 1
        print(f"  vuelta {contador[0]}")
        if contador[0] == 3:
            raise SenalBreak()

    bucle_while(lambda: contador[0] < 10, [cuerpo_1])
    print(f"  salió con contador = {contador[0]}  (se detuvo en 3, no llegó a 10)\n")

    # -----------------------------------------------------------------
    # Demo 2: break CON etiqueta, atravesando un ciclo anidado
    #
    #   'externo: while true do
    #        while true do
    #            break 'externo;      <- debe salir de LOS DOS ciclos
    #            ...esto no se ejecuta...
    #        ...esto TAMPOCO se ejecuta, es parte del ciclo externo...
    #   ...aquí sí continúa el programa...
    # -----------------------------------------------------------------
    print("Demo 2: break con etiqueta, atraviesa dos ciclos")
    rastro = []

    def cuerpo_interno():
        rastro.append('interno')
        if len(rastro) == 2:
            # Le pide salir al ciclo llamado 'externo', no al que lo
            # contiene directamente.
            raise SenalBreak('externo')

    def cuerpo_externo():
        rastro.append('externo-antes')
        # Este ciclo interno usa etiqueta='interno'. El SenalBreak('externo')
        # que lance cuerpo_interno NO le pertenece (su etiqueta no calza),
        # así que lo vuelve a lanzar (`raise` sin argumentos, dentro del
        # except de bucle_while) en vez de detenerse él mismo.
        bucle_while(lambda: True, [cuerpo_interno], etiqueta='interno')
        # Esta línea NUNCA se ejecuta: la excepción ya se escapó del
        # ciclo interno y atraviesa esta función sin pasar por aquí.
        rastro.append('externo-despues')

    bucle_while(lambda: True, [cuerpo_externo], etiqueta='externo')
    print(f"  rastro = {rastro}")
    print("  ('externo-despues' NUNCA aparece: la señal se saltó todo lo")
    print("   que quedaba en el ciclo externo, hasta encontrar su etiqueta)\n")

    # -----------------------------------------------------------------
    # Demo 3: return atravesando un while sin ser atrapado por él
    # -----------------------------------------------------------------
    print("Demo 3: return atraviesa un while de largo")

    def buscar_primer_par(numeros):
        indice = [0]

        def condicion():
            return indice[0] < len(numeros)

        def cuerpo():
            valor = numeros[indice[0]]
            indice[0] += 1
            if valor % 2 == 0:
                raise SenalReturn(valor)

        try:
            bucle_while(condicion, [cuerpo])
            return None   # se recorrió todo el ciclo sin encontrar nada
        except SenalReturn as señal:
            # Aquí, y solo aquí (el límite de la "función"), se atrapa el
            # return. bucle_while ni se enteró: la señal lo atravesó.
            return señal.valor

    print(f"  buscar_primer_par([1, 3, 5, 8, 9]) = {buscar_primer_par([1, 3, 5, 8, 9])}")

    # -------------------------------------------------------------------
    # Para su proyecto:
    #
    # - `While.ejecutar` y `Repeat.ejecutar` van a tener el mismo `try` de
    #   `bucle_while` de aquí arriba: atrapan Break/Continue que les
    #   correspondan, y dejan pasar SenalReturn sin tocarla.
    # - La llamada a una función (que todavía no existe — es la Sesión 4)
    #   es quien finalmente atrapa SenalReturn, del mismo modo que
    #   `buscar_primer_par` lo hace aquí con su propio `try`.
    # - Fíjense que ninguna de las funciones intermedias (`ejecutar_bloque`,
    #   `cuerpo_externo`) tuvo que saber NADA sobre señales para que esto
    #   funcione. Eso es lo que hace que esta técnica escale sin ensuciar
    #   cada nodo del AST con banderas.
    # -------------------------------------------------------------------
