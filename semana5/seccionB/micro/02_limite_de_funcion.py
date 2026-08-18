"""
MICRO-EJEMPLO 2: La llamada a función como límite de pila.

En micro/01_senales.py (Sesión 3) ya vieron que `SenalReturn` debe
atravesar un `while` sin que este la atrape, y que la llamada de función
—que todavía no existía— iba a ser quien la atrapara. Eso ya lo tienen.

Lo que falta, y es la trampa fácil de no ver: si una llamada a función
atrapa SenalReturn pero se OLVIDA de atrapar también SenalBreak y
SenalContinue, un `break` mal puesto DENTRO del cuerpo de una función
(fuera de cualquier ciclo de esa función — un error del programador de
MiniPascal) se escapa de la llamada... y sigue subiendo hasta encontrar
el primer `while` que SÍ lo atrape, que puede ser el del PROGRAMA QUE
LLAMÓ a la función. Un error de sintaxis-fantasma adentro de una función
terminaría cortando un ciclo que no tiene nada que ver.

Correr con: python3 02_limite_de_funcion.py
"""


class SenalBreak(Exception):
    pass


class SenalReturn(Exception):
    def __init__(self, valor):
        self.valor = valor


def bucle_while(condicion, cuerpo):
    """Simula While.ejecutar: atrapa SenalBreak, deja pasar SenalReturn."""
    while condicion():
        try:
            cuerpo()
        except SenalBreak:
            break
        # Sin `except SenalReturn` a propósito: un while nunca debe
        # absorber un return, tiene que dejarlo subir.


def llamar_mal(cuerpo_funcion):
    """Simula Llamada.evaluar CON EL BUG: solo atrapa SenalReturn. Si un
    break se escapa del cuerpo de la función, sigue de largo."""
    try:
        cuerpo_funcion()
        return None
    except SenalReturn as señal:
        return señal.valor
    # Falta: except SenalBreak (y SenalContinue). A propósito, para ver
    # qué pasa sin ellos.


def llamar_bien(cuerpo_funcion):
    """Simula Llamada.evaluar CORRECTO: la llamada es un límite de pila
    completo. Atrapa SenalReturn (el caso normal) Y convierte un
    Break/Continue perdido en un error semántico, en vez de dejarlo
    escapar hacia quien llamó."""
    try:
        cuerpo_funcion()
        return None
    except SenalReturn as señal:
        return señal.valor
    except SenalBreak:
        print("    [Error Semántico] 'break' usado fuera de un ciclo.")
        return None


if __name__ == '__main__':
    print("Escenario: una función con un 'break' escrito fuera de cualquier")
    print("ciclo (un error de quien programó en MiniPascal), llamada desde")
    print("DENTRO de un while del programa principal.\n")

    def cuerpo_funcion_con_bug():
        # Un break sin ningún while/repeat que lo contenga DENTRO de esta
        # función. Debería reportarse como error semántico ahí mismo, sin
        # afectar a nadie más.
        raise SenalBreak()

    print("Con llamar_mal (el bug):\n")
    contador = [0]

    def cuerpo_while_malo():
        contador[0] += 1
        print(f"  vuelta {contador[0]}")
        llamar_mal(cuerpo_funcion_con_bug)   # el break de adentro "se cuela"
        print("  (esta línea nunca se imprime, ni siquiera en la vuelta 1)")

    bucle_while(lambda: contador[0] < 5, cuerpo_while_malo)
    print(f"\n  El while se detuvo en la vuelta {contador[0]} — ¡nunca llegó a 5!")
    print("  El break estaba DENTRO de la función, pero como llamar_mal no lo")
    print("  atrapó, siguió subiendo hasta cortar el ciclo de QUIEN LA LLAMÓ.")
    print("  Ese no era el ciclo al que pertenecía.\n")

    print("Con llamar_bien (correcto):\n")
    contador2 = [0]

    def cuerpo_while_bueno():
        contador2[0] += 1
        print(f"  vuelta {contador2[0]}")
        llamar_bien(cuerpo_funcion_con_bug)

    bucle_while(lambda: contador2[0] < 5, cuerpo_while_bueno)
    print(f"\n  El while llegó hasta la vuelta {contador2[0]}, como debía — el")
    print("  break se convirtió en error DENTRO de la llamada, y no salió de ahí.")

    # -------------------------------------------------------------------
    # Para su proyecto:
    #
    # - `Llamada.evaluar` (ast_nodes.py) es exactamente `llamar_bien`:
    #   atrapa SenalReturn (el caso normal) Y SenalBreak/SenalContinue (el
    #   caso de un break/continue perdido dentro de una función), y
    #   reporta este segundo caso como error semántico en vez de dejarlo
    #   escapar.
    # - Es el mismo patrón que `Programa.ejecutar` ya usaba desde la
    #   Sesión 3 para un break FUERA de cualquier función: una llamada a
    #   función es un límite de pila igual de real que el programa
    #   completo — solo que ocurre muchas veces durante una ejecución, no
    #   una sola vez al final.
    # -------------------------------------------------------------------
