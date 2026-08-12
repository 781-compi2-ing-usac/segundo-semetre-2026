from .visitante import *
from .expresiones import * 
from .tabla_simbolos import *

class Interprete(Visitor):
    
    tablaRaiz = TablaSimbolo()
    tablaSimbolos = tablaRaiz

    def visit_expresion_binaria(self, binaria):
        if (binaria.operador == "+"):
            val1 = binaria.exp1.accept(self)
            val2 = binaria.exp2.accept(self)
            val_tipo = 'int'
            if val1.tipo == 'float' or val2.tipo == 'float':
                val_tipo = 'float'
            #print("suma", val1, val2)
            return ExpresionValor(val1.val + val2.val, val_tipo)
        elif (binaria.operador == "-"):
            val1 = binaria.exp1.accept(self)
            val2 = binaria.exp2.accept(self)
            val_tipo = 'int'
            if (val1.tipo == 'float' or val2.tipo == 'float'):
                val_tipo = 'float'
            #print("suma", val1, val2)
            return ExpresionValor(val1.val - val2.val, val_tipo)
        elif (binaria.operador == "*"):
            val1 = binaria.exp1.accept(self)
            val2 = binaria.exp2.accept(self)
            #print("multiplicacion", val1.val, val2.val,val1.tipo, val2.tipo )
            val_tipo = 'int'
            if val1.tipo == 'float' or val2.tipo == 'float':
                val_tipo = 'float'
            #print("suma", val1, val2)
            return ExpresionValor(val1.val * val2.val, val_tipo)


    
    def visit_expresion_valor(self, valor):
        if valor.tipo == 'identificador':
            ## buscamos el valor
            valor_final = self.tablaSimbolos.buscar(valor.val)
            if valor_final.tipo == 'funcion':
                valor_finall.accept(self)
            return valor_final
        #print("valor final", valor.val)
        return ExpresionValor(valor.val, valor.tipo)


    def visit_asignacion(self, asignacion):
        valor_resuelto = asignacion.exp.accept(self)
        if asignacion.tipo == valor_resuelto.tipo:
            self.tablaSimbolos.insertar(asignacion.identificador,valor_resuelto,valor_resuelto.tipo) 
        else:
            print('ERROR DE TIPO',asignacion.tipo, valor_resuelto.tipo)
        #print(self.tablaSimbolos)
        
        #return self.tablaSimbolos

    def visit_condicional(self, condicional):
        expresion = condicional.exp.accept(self)

        ## crear nueva tabla de simbolos
        self.tablaSimbolos = TablaSimbolo(self.tablaSimbolos)

        if expresion.val:
            for instr in condicional.instrucciones:
                #retorna algo??? usualmente si
                resultado = instr.accept(self)
                #si resultado es algo que sucede?
            self.tablaSimbolos = self.tablaSimbolos.padre
            return resultado
        self.tablaSimbolos = self.tablaSimbolos.padre
        return None #si no pasa nada

#### FLUJO DE CONTROL DEBE RETORNAR EL ESTADO DE FINALIZACION
#function funcioncita() {
#    if expr {
#       return 3
#    }
#}
#funcion -> if -> return
# FLUJO DEL VALOR DE RETORNO
#return -> IF -> FUNCION

    def visit_imprimir(self, valor):
        # En este caso imprimimos directamente a consola, en la practica
        # deberian estar concatenando a un string de salida que es lo que estarian
        # retornando desde su API
        val = valor.exp.accept(self)
        if val == None: 
            print( 'stdout::', None)
            return
        print('stdout::', val.val)
        #return ExpresionValor(valor.val, valor.tipo)
    
    
    # funciones

    def visit_funcion_dcl(self, funcion):

        
        self.tablaSimbolos.insertar(funcion.identificador,
            funcion,
            'funcion') 

        return None #si no pasa nada


    def visit_funcion_exec(self, funcion):
        # RECUPERAMOS LASINSTRUCCIONES DE LA FUNCION
        bloquefuncion = self.tablaSimbolos.buscar(funcion.identificador)
        
        ##### PARAMETROS: VALIDAMOS SI ES QUE HAY
        # en este punto
        # realizamos la validacion de parametros
        #######

        ## crear nueva tabla de simbolos
        self.tablaSimbolos = TablaSimbolo(self.tablaSimbolos)
        #### INSERTAMOS LOS PARAMETROS EN LA TABLA CON EL NUEVO SCOPE
        

        for instr in bloquefuncion.instrucciones:
            #retorna algo??? usualmente si
            resultado = instr.accept(self)
            
            #if resultado == 'return_instr'
            #   return resultado
            #si resultado es algo que sucede?
            #por ejemplo
            # if type(resultado)  == 'Return'

        self.tablaSimbolos = self.tablaSimbolos.padre
        return None #si no pasa nada