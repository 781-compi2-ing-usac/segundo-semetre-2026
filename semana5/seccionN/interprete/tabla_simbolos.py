

class Registro():
    def __init__(self, identificador, tipo, valor):
        self.identificador = identficador
        self.tipo = tipo
        self.valor = valor


class TablaSimbolo():

    def __init__(self, padre  = None):
        self.padre = padre #Deberia ser  un objeto TablaSimbolo
        self.tabla = {}

    def insertar(self, llave, valor, tipo):
        #Aqui hacemos la validacion de tipo
        # un posible tip es agregar el tipo como parte del valor a almacenar
        # en este caso, como un array [valor,tipo]
        self.tabla[llave] = [valor, tipo]

    def buscar(self, llave):
        
        if not (llave in self.tabla):
            if self.padre == None:
                return None
            #print('tablapadre', self.padre.tabla)
            busquedaExtendida = self.padre.buscar(llave)
            if busquedaExtendida == None:
                return None
            return busquedaExtendida
        #print('tabla actual', self.tabla)
        
        return self.tabla[llave][0]

    def get_new_type(self, llave):
        #creamos un nuevo metodo para obtener los tipos definidos por el usuario
        print('buscando nuevo tipo')
        if not (llave in self.tabla):
            if self.padre == None:
                return None
            #print('tablapadre', self.padre.tabla)
            busquedaExtendida = self.padre.buscar(llave)
            if busquedaExtendida == None:
                return None
            return busquedaExtendida
        #print('tabla actual', self.tabla)
        print(self.tabla[llave][1])

        return self.tabla[llave][1]

    def actualizar(self, llave, valor):
        # funcion necesaria para las variables tipo mut
        pass