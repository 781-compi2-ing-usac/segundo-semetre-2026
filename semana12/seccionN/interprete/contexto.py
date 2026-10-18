class ContextoControl:
    def __init__(self):
        self._marcos = []

    def entrar_bucle(self, inicio, fin):
        self._marcos.append({'kind': 'bucle', 'inicio': inicio, 'fin': fin})

    def salir_bucle(self):
        if not self._marcos or self._marcos[-1]['kind'] != 'bucle':
            raise RuntimeError('salir_bucle sin bucle activo')
        return self._marcos.pop()

    def bucle_actual(self):
        for marco in reversed(self._marcos):
            if marco['kind'] == 'bucle':
                return (marco['inicio'], marco['fin'])
        return None

    def entrar_funcion(self, fin, nombre):
        self._marcos.append({'kind': 'funcion', 'fin': fin, 'nombre': nombre})

    def salir_funcion(self):
        if not self._marcos or self._marcos[-1]['kind'] != 'funcion':
            raise RuntimeError('salir_funcion sin funcion activa')
        return self._marcos.pop()

    def funcion_actual(self):
        for marco in reversed(self._marcos):
            if marco['kind'] == 'funcion':
                return marco
        return None
