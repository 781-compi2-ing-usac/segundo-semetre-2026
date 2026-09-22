"""
MiniPascal v6 — El intérprete, ahora como VISITANTE.

Este archivo no tiene ni una idea nueva. Es, línea por línea, la misma
lógica que hasta la Sesión 5 vivía repartida dentro de `ast_nodes.py`,
solo que MUDADA aquí. Comparen con `diff` contra
semana6/seccionB/minipascal/ast_nodes.py y van a reconocer cada bloque.

La traducción fue mecánica, y es exactamente la que ustedes van a hacer
con su Proyecto 1:

    ANTES, en ast_nodes.py           AHORA, en interprete.py
    ----------------------           -----------------------
    class Literal:                   class Interprete(Visitante):
        def evaluar(self, entorno,       def visitar_Literal(self, nodo):
                    errores, tabla):         return nodo.valor
            return self.valor

    self.valor        ->   nodo.valor
    entorno           ->   self.entorno
    errores           ->   self.errores
    tabla             ->   self.tabla
    hijo.evaluar(...) ->   hijo.aceptar(self)
    hijo.ejecutar(...)->   hijo.aceptar(self)

Eso es todo. Búsqueda y reemplazo, básicamente. Si el refactor salió
bien, los 9 ejemplos de las Sesiones 1-5 tienen que dar EXACTAMENTE la
misma salida que antes — ese es el criterio, y por eso los ejemplos
`.mpas` no se tocaron.


Lo único que sí cambió de verdad
--------------------------------
`self.entorno` es ahora un atributo que se mueve. Antes, cada llamada
recibía su entorno como parámetro y el de quien llamaba quedaba intacto
solo. Ahora hay UN entorno "actual" y hay que acordarse de restaurarlo
al salir de un bloque o de una función. Vean `visitar_Bloque` y
`visitar_Llamada`: los dos usan try/finally.

Ese `finally` no es decorativo. Sin él, un `break` o un `return` que sale
de un bloque dejaría a `self.entorno` apuntando al entorno de adentro, y
el resto del programa se ejecutaría en el ámbito equivocado.
"""

from ast_nodes import Funcion, TipoRegistro
from entorno import Entorno
from senales import SenalBreak, SenalContinue, SenalReturn
from valores import (
    FuncionValor, VALORES_POR_DEFECTO, TIPOS_INDEXABLES, VistaArreglo,
    describir_tipo, formatear, tipo_de_valor,
)
from visitante import Visitante


TIPOS_SUMA = {
    ('integer', 'integer'): 'integer',
    ('integer', 'real'):    'real',
    ('real',    'integer'): 'real',
    ('real',    'real'):    'real',
    ('string',  'string'):  'string',
}

TIPOS_MENOR = {
    ('integer', 'integer'): 'boolean',
    ('integer', 'real'):    'boolean',
    ('real',    'integer'): 'boolean',
    ('real',    'real'):    'boolean',
    ('string',  'string'):  'boolean',
}

# Funciones embebidas (built-ins). Un solo caso representativo: `length`,
# que sirve tanto para arreglos como para cadenas porque en Python ambos
# responden a `len()`. Se resuelven ANTES de mirar el entorno.
FUNCIONES_EMBEBIDAS = {
    'length': len,
}


class Interprete(Visitante):
    """Recorre el AST y lo EJECUTA."""

    etiqueta = 'intérprete'

    def __init__(self, entorno=None, errores=None, tabla=None):
        # Los tres estados que antes viajaban como parámetros.
        self.entorno = entorno if entorno is not None else Entorno()
        self.errores = errores
        self.tabla = tabla

    # -- utilidades internas ------------------------------------------------

    def error(self, nodo, mensaje):
        self.errores.agregar('Semántico', mensaje, nodo.linea, nodo.columna)

    def en_entorno(self, nuevo_entorno, accion):
        """Ejecuta `accion()` con `nuevo_entorno` como entorno actual, y
        restaura el anterior pase lo que pase (incluidas las señales de
        break/continue/return, que son excepciones)."""
        anterior = self.entorno
        self.entorno = nuevo_entorno
        try:
            return accion()
        finally:
            self.entorno = anterior

    def condicion_booleana(self, valor, nodo, de_donde):
        if valor is None:
            return False
        if tipo_de_valor(valor) != 'boolean':
            self.error(nodo, f"La condición de {de_donde} debe ser de tipo "
                             f"boolean, no {tipo_de_valor(valor)}.")
            return False
        return True

    def arreglo_de(self, nodo, nombre, verbo):
        """Busca `nombre` y comprueba que sea indexable. Devuelve el
        arreglo, o None si hubo error (ya reportado)."""
        if not self.entorno.existe(nombre):
            self.error(nodo, f"El arreglo '{nombre}' no ha sido declarado.")
            return None
        arreglo = self.entorno.buscar(nombre)
        if not isinstance(arreglo, TIPOS_INDEXABLES):
            self.error(nodo, f"'{nombre}' no es un arreglo, no se puede {verbo}.")
            return None
        return arreglo

    def registro_de(self, nodo):
        """Busca `nodo.nombre_objeto` y comprueba que sea un registro con
        el campo `nodo.nombre_campo`. Igual para leer y para escribir."""
        if not self.entorno.existe(nodo.nombre_objeto):
            self.error(nodo, f"'{nodo.nombre_objeto}' no ha sido declarado.")
            return None
        objeto = self.entorno.buscar(nodo.nombre_objeto)
        if not isinstance(objeto, dict):
            self.error(nodo, f"'{nodo.nombre_objeto}' no es un registro, "
                             f"no tiene campos.")
            return None
        if nodo.nombre_campo not in objeto:
            self.error(nodo, f"'{nodo.nombre_objeto}' no tiene un campo "
                             f"llamado '{nodo.nombre_campo}'.")
            return None
        return objeto

    # -- EXPRESIONES --------------------------------------------------------

    def visitar_Literal(self, nodo):
        return nodo.valor

    def visitar_Variable(self, nodo):
        if not self.entorno.existe(nodo.nombre):
            self.error(nodo, f"La variable '{nodo.nombre}' no ha sido declarada.")
            return None
        return self.entorno.buscar(nodo.nombre)

    def visitar_Aritmetica(self, nodo):
        izq = nodo.izquierdo.aceptar(self)
        der = nodo.derecho.aceptar(self)

        if izq is None or der is None:
            return None

        if nodo.operador == '+':
            tipo_resultado = TIPOS_SUMA.get((tipo_de_valor(izq), tipo_de_valor(der)))
            if tipo_resultado is None:
                self.error(nodo, f"No es posible aplicar el operador '+' entre "
                                 f"los tipos {tipo_de_valor(izq)} y "
                                 f"{tipo_de_valor(der)}.")
                return None
            return izq + der

        if nodo.operador == '-':
            return izq - der
        if nodo.operador == '*':
            return izq * der
        if nodo.operador == '/':
            return izq / der

        raise ValueError(f"Operador desconocido: {nodo.operador}")

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ (viene desde la Sesión 2, sigue igual):
        # Solo `+` está protegido con tabla de tipos. Repliquen el mismo
        # patrón para `-`, `*`, `/`.
        # ------------------------------------------------------------------

    def visitar_Negacion(self, nodo):
        valor = nodo.expresion.aceptar(self)
        if valor is None:
            return None
        return -valor

    def visitar_Comparacion(self, nodo):
        izq = nodo.izquierdo.aceptar(self)
        der = nodo.derecho.aceptar(self)

        if izq is None or der is None:
            return None

        if nodo.operador == '<':
            if TIPOS_MENOR.get((tipo_de_valor(izq), tipo_de_valor(der))) is None:
                self.error(nodo, f"No es posible comparar los tipos "
                                 f"{tipo_de_valor(izq)} y {tipo_de_valor(der)} "
                                 f"con '<'.")
                return None
            return izq < der

        if nodo.operador == '==':
            return izq == der
        if nodo.operador == '!=':
            return izq != der
        if nodo.operador == '>':
            return izq > der
        if nodo.operador == '<=':
            return izq <= der
        if nodo.operador == '>=':
            return izq >= der

        raise ValueError(f"Operador desconocido: {nodo.operador}")

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ (viene desde la Sesión 3, sigue igual):
        # Solo `<` tiene tabla de tipos.
        # ------------------------------------------------------------------

    def visitar_Llamada(self, nodo):
        valores = []
        for argumento in nodo.argumentos:
            valor = argumento.aceptar(self)
            if valor is None:
                return None
            valores.append(valor)

        if nodo.nombre in FUNCIONES_EMBEBIDAS:
            try:
                return FUNCIONES_EMBEBIDAS[nodo.nombre](*valores)
            except TypeError:
                # `len()` lanza TypeError por DOS causas distintas:
                # cantidad de argumentos incorrecta, o un argumento de un
                # tipo que no soporta. Las distinguimos con la cantidad,
                # que sí podemos comprobar nosotros mismos — así el
                # mensaje no le echa la culpa a la cantidad cuando en
                # realidad es el tipo el que está mal.
                if len(valores) != 1:
                    self.error(nodo, f"'{nodo.nombre}' espera 1 argumento, "
                                     f"recibió {len(valores)}.")
                else:
                    self.error(nodo, f"'{nodo.nombre}' no admite un argumento "
                                     f"de tipo "
                                     f"{tipo_de_valor(valores[0]) or 'desconocido'}.")
                return None

        if not self.entorno.existe(nodo.nombre):
            self.error(nodo, f"La función '{nodo.nombre}' no ha sido declarada.")
            return None

        funcion = self.entorno.buscar(nodo.nombre)
        if not isinstance(funcion, FuncionValor):
            self.error(nodo, f"'{nodo.nombre}' no es una función, no se puede llamar.")
            return None

        if len(valores) != len(funcion.parametros):
            self.error(nodo, f"'{nodo.nombre}' espera {len(funcion.parametros)} "
                             f"argumento(s), recibió {len(valores)}.")
            return None

        # *** El corazón de la Sesión 4, sin cambios ***
        # padre=funcion.entorno_definicion, NUNCA padre=self.entorno. Si
        # colgara del entorno de QUIEN LLAMA, cualquier variable local de
        # quien llama sería visible por accidente dentro de la función —
        # scoping dinámico. Colgar del entorno donde la función fue
        # declarada es lo mismo que hace un cierre en Python o JavaScript.
        entorno_activacion = Entorno(padre=funcion.entorno_definicion, ambito=nodo.nombre)
        for parametro, valor in zip(funcion.parametros, valores):
            # Todo se pasa por VALOR, incluidos los arreglos. A un
            # VistaArreglo (un slice) esto A PROPÓSITO no lo toca: un
            # slice nunca copia, ni siquiera al cruzar una llamada.
            if isinstance(valor, list):
                valor = list(valor)
            elif isinstance(valor, dict):
                valor = dict(valor)
            entorno_activacion.declarar(parametro.nombre, valor, tipo=parametro.tipo)

        def correr_cuerpo():
            try:
                funcion.cuerpo.aceptar(self)
            except SenalReturn as señal:
                return señal.valor
            except SenalBreak as señal:
                self.errores.agregar('Semántico', "'break' usado fuera de un ciclo.",
                                     señal.linea, señal.columna)
            except SenalContinue as señal:
                self.errores.agregar('Semántico', "'continue' usado fuera de un ciclo.",
                                     señal.linea, señal.columna)
            # El cuerpo terminó sin pasar por ningún `return`. LO QUE FALTA
            # AQUÍ: un compilador de verdad exigiría que TODO camino posible
            # termine en return; aquí solo devolvemos el valor por defecto.
            return VALORES_POR_DEFECTO.get(funcion.tipo_retorno)

        return self.en_entorno(entorno_activacion, correr_cuerpo)

    def visitar_Slice(self, nodo):
        arreglo = self.arreglo_de(nodo, nodo.nombre, 'tomar un slice')
        if arreglo is None:
            return None

        inicio = nodo.inicio.aceptar(self)
        fin = nodo.fin.aceptar(self)
        if inicio is None or fin is None:
            return None

        if not (0 <= inicio <= fin <= len(arreglo)):
            self.error(nodo, f"Rango [{inicio}..{fin}) inválido para "
                             f"'{nodo.nombre}' (tamaño {len(arreglo)}).")
            return None

        # Si `arreglo` YA es una VistaArreglo (un slice de un slice), la
        # nueva vista sigue apuntando al arreglo ORIGINAL de verdad.
        if isinstance(arreglo, VistaArreglo):
            return VistaArreglo(arreglo.arreglo_original,
                                arreglo.inicio + inicio, arreglo.inicio + fin)
        return VistaArreglo(arreglo, inicio, fin)

    def visitar_Indexado(self, nodo):
        arreglo = self.arreglo_de(nodo, nodo.nombre, 'indexar')
        if arreglo is None:
            return None

        indice = nodo.indice.aceptar(self)
        if indice is None:
            return None

        if not (0 <= indice < len(arreglo)):
            self.error(nodo, f"Índice {indice} fuera de rango para "
                             f"'{nodo.nombre}' (tamaño {len(arreglo)}).")
            return None

        return arreglo[indice]

    def visitar_AccesoCampo(self, nodo):
        objeto = self.registro_de(nodo)
        if objeto is None:
            return None
        return objeto[nodo.nombre_campo]

    # -- INSTRUCCIONES ------------------------------------------------------

    def visitar_Writeln(self, nodo):
        valor = nodo.expresion.aceptar(self)
        if valor is None:
            return
        print(formatear(valor))

    def visitar_Declaracion(self, nodo):
        if nodo.expresion_inicial is not None:
            valor = nodo.expresion_inicial.aceptar(self)
            if valor is None:
                valor = VALORES_POR_DEFECTO.get(nodo.tipo)
        else:
            valor = VALORES_POR_DEFECTO.get(nodo.tipo)

        self.entorno.declarar(nodo.nombre, valor, tipo=nodo.tipo,
                              constante=nodo.constante)

        self.tabla.registrar(
            nombre=nodo.nombre,
            categoria='Constante' if nodo.constante else 'Variable',
            tipo=nodo.tipo,
            ambito=self.entorno.ambito,
            linea=nodo.linea,
            valor=valor,
        )

    def visitar_DeclaracionInferida(self, nodo):
        valor = nodo.expresion.aceptar(self)
        if valor is None:
            return   # el error ya se reportó al evaluar la expresión

        tipo = describir_tipo(valor)
        self.entorno.declarar(nodo.nombre, valor, tipo=tipo, constante=nodo.constante)

        self.tabla.registrar(
            nombre=nodo.nombre,
            categoria='Constante' if nodo.constante else 'Variable',
            tipo=tipo,
            ambito=self.entorno.ambito,
            linea=nodo.linea,
            # La tabla guarda una FOTO del momento, no un espejo en vivo
            # del slice (ver README de la Sesión 2).
            valor=list(valor) if isinstance(valor, VistaArreglo) else valor,
        )

    def visitar_DeclaracionArreglo(self, nodo):
        valor_por_defecto = VALORES_POR_DEFECTO.get(nodo.tipo_elemento)
        # Multiplicar una lista de un solo elemento SOLO es seguro porque
        # los valores por defecto son todos inmutables.
        valores = [valor_por_defecto] * nodo.tamano
        tipo_declarado = f'array[{nodo.tamano}] of {nodo.tipo_elemento}'

        self.entorno.declarar(nodo.nombre, valores, tipo=tipo_declarado, constante=False)

        self.tabla.registrar(
            nombre=nodo.nombre,
            categoria='Arreglo',
            tipo=tipo_declarado,
            ambito=self.entorno.ambito,
            linea=nodo.linea,
            valor=list(valores),   # una FOTO, no la misma lista que se muta después
        )

    def visitar_Asignacion(self, nodo):
        valor = nodo.expresion.aceptar(self)
        if valor is None:
            return

        if not self.entorno.existe(nodo.nombre):
            self.error(nodo, f"La variable '{nodo.nombre}' no ha sido declarada.")
            return

        if self.entorno.es_constante(nodo.nombre):
            self.error(nodo, f"No es posible modificar la variable "
                             f"'{nodo.nombre}' porque fue declarada como inmutable.")
            return

        self.entorno.asignar(nodo.nombre, valor)

    def visitar_AsignacionIndexada(self, nodo):
        arreglo = self.arreglo_de(nodo, nodo.nombre, 'indexar')
        if arreglo is None:
            return

        indice = nodo.indice.aceptar(self)
        valor = nodo.expresion.aceptar(self)
        if indice is None or valor is None:
            return

        if not (0 <= indice < len(arreglo)):
            self.error(nodo, f"Índice {indice} fuera de rango para "
                             f"'{nodo.nombre}' (tamaño {len(arreglo)}).")
            return

        # `arreglo` es el MISMO objeto que vive dentro de `Entorno`:
        # mutamos la casilla, no reemplazamos el arreglo completo. Si es
        # una VistaArreglo, su `__setitem__` traduce esto a una escritura
        # sobre el arreglo ORIGINAL.
        arreglo[indice] = valor

    def visitar_AsignacionCampo(self, nodo):
        objeto = self.registro_de(nodo)
        if objeto is None:
            return

        valor = nodo.expresion.aceptar(self)
        if valor is None:
            return

        objeto[nodo.nombre_campo] = valor

    def visitar_Bloque(self, nodo):
        def correr():
            for instruccion in nodo.instrucciones:
                instruccion.aceptar(self)

        self.en_entorno(Entorno(padre=self.entorno), correr)

    def visitar_If(self, nodo):
        valor = nodo.condicion.aceptar(self)
        if not self.condicion_booleana(valor, nodo, "un 'if'"):
            return
        if valor:
            nodo.bloque_si.aceptar(self)
        elif nodo.bloque_no is not None:
            nodo.bloque_no.aceptar(self)

    def visitar_While(self, nodo):
        while True:
            valor = nodo.condicion.aceptar(self)
            if not self.condicion_booleana(valor, nodo, "un 'while'"):
                return
            if not valor:
                break

            try:
                nodo.cuerpo.aceptar(self)
            except SenalContinue as señal:
                if señal.etiqueta not in (None, nodo.etiqueta):
                    raise
                continue
            except SenalBreak as señal:
                if señal.etiqueta not in (None, nodo.etiqueta):
                    raise
                break
            # SenalReturn NO se atrapa aquí — tiene que atravesar este
            # `while` sin tocarlo y seguir subiendo hasta la Llamada que la
            # originó. Igual que en semana4/seccionB/micro/01_senales.py.

    def visitar_Repeat(self, nodo):
        def correr():
            while True:
                try:
                    for instruccion in nodo.instrucciones:
                        instruccion.aceptar(self)
                except SenalContinue as señal:
                    if señal.etiqueta is not None:
                        raise
                except SenalBreak as señal:
                    if señal.etiqueta is not None:
                        raise
                    break

                valor = nodo.condicion.aceptar(self)
                if not self.condicion_booleana(valor, nodo, "un 'repeat...until'"):
                    return
                if valor:
                    break

        self.en_entorno(Entorno(padre=self.entorno), correr)

    def visitar_Case(self, nodo):
        valor = nodo.selector.aceptar(self)
        if valor is None:
            return

        for rama in nodo.ramas:
            if valor == rama.valor:
                rama.bloque.aceptar(self)
                return

        if nodo.bloque_por_defecto is not None:
            nodo.bloque_por_defecto.aceptar(self)

    def visitar_RamaCase(self, nodo):
        # `visitar_Case` entra directo al bloque de la rama que coincide,
        # así que este método no se usa al ejecutar. Existe para que
        # ningún nodo quede sin su `visitar_X` — y para que el día que
        # escriban un visitante que SÍ recorra el árbol completo (un
        # verificador de tipos, por ejemplo) ya tenga dónde engancharse.
        nodo.bloque.aceptar(self)

    def visitar_Break(self, nodo):
        raise SenalBreak(nodo.etiqueta, nodo.linea, nodo.columna)

    def visitar_Continue(self, nodo):
        raise SenalContinue(nodo.etiqueta, nodo.linea, nodo.columna)

    def visitar_Funcion(self, nodo):
        # Declarar una función es lo mismo que declarar una variable:
        # guardar algo bajo un nombre en el `Entorno`. Lo que se guarda es
        # un FuncionValor — la declaración MÁS el entorno donde nació, que
        # es la pieza que hace posible el scoping estático. Declararla NO
        # ejecuta su cuerpo.
        self.entorno.declarar(nodo.nombre, FuncionValor(nodo, self.entorno),
                              tipo='function', constante=True)

        firma = ', '.join(f'{p.nombre}: {p.tipo}' for p in nodo.parametros)
        self.tabla.registrar(
            nombre=nodo.nombre,
            categoria='Función',
            tipo=f'({firma}) -> {nodo.tipo_retorno}',
            ambito=self.entorno.ambito,
            linea=nodo.linea,
            valor='<función>',
        )

    def visitar_Parametro(self, nodo):
        # Un parámetro no se "ejecuta": lo lee `visitar_Llamada` (para
        # armar el entorno de activación) y `visitar_TipoRegistro` (para
        # saber qué campos tiene el record). Igual que RamaCase, existe
        # para no dejar huecos en el patrón.
        return nodo

    def visitar_Return(self, nodo):
        valor = nodo.expresion.aceptar(self)
        raise SenalReturn(valor, nodo.linea, nodo.columna)

    def visitar_TipoRegistro(self, nodo):
        # Declarar un TIPO también es guardar algo bajo un nombre. Aquí el
        # "valor" es la propia definición — el nodo del AST — porque un
        # tipo no es algo que exista en tiempo de ejecución.
        self.entorno.declarar(nodo.nombre, nodo, tipo='record-type', constante=True)

        firma = ', '.join(f'{c.nombre}: {c.tipo}' for c in nodo.campos)
        self.tabla.registrar(
            nombre=nodo.nombre,
            categoria='Tipo',
            tipo=f'record {{ {firma} }}',
            ambito=self.entorno.ambito,
            linea=nodo.linea,
            valor='<tipo>',
        )

    def visitar_DeclaracionRegistro(self, nodo):
        if not self.entorno.existe(nodo.nombre_tipo):
            self.error(nodo, f"El tipo '{nodo.nombre_tipo}' no ha sido declarado.")
            return

        definicion = self.entorno.buscar(nodo.nombre_tipo)
        if not isinstance(definicion, TipoRegistro):
            self.error(nodo, f"'{nodo.nombre_tipo}' no es un tipo record.")
            return

        valores = {campo.nombre: VALORES_POR_DEFECTO.get(campo.tipo)
                   for campo in definicion.campos}
        self.entorno.declarar(nodo.nombre, valores, tipo=nodo.nombre_tipo,
                              constante=False)

        self.tabla.registrar(
            nombre=nodo.nombre,
            categoria='Registro',
            tipo=nodo.nombre_tipo,
            ambito=self.entorno.ambito,
            linea=nodo.linea,
            valor=dict(valores),   # una FOTO, igual que con los arreglos
        )

    # -- RAÍZ ---------------------------------------------------------------

    def visitar_Programa(self, nodo):
        try:
            nodo.bloque.aceptar(self)
        except SenalBreak as señal:
            self.errores.agregar('Semántico', "'break' usado fuera de un ciclo.",
                                 señal.linea, señal.columna)
        except SenalContinue as señal:
            self.errores.agregar('Semántico', "'continue' usado fuera de un ciclo.",
                                 señal.linea, señal.columna)
        except SenalReturn as señal:
            self.errores.agregar('Semántico', "'return' usado fuera de una función.",
                                 señal.linea, señal.columna)
