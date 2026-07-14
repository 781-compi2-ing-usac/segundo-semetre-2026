# Instalación de Requerimientos para el Proyecto

Antes de todo esto, recordemos que el proyecto será desarrollado en un sistema operativo Linux, por lo que se recomienda las distribuciones basadas en Debian, como Ubuntu o Linux Mint. En última instacia, se puede hacer uso de WSL (Windows Subsystem for Linux) en caso de que se esté trabajando en un sistema operativo Windows.

## Requerimientos
- Python 3.11 o mayor
- Pip 23.0.1 o mayor
- PLY 3.11 o mayor

## Instalación de Python (En linux)
Normalmente las distribuciones de Linux ya traen Python preinstalado, sin embargo, en caso de que no se tenga instalado, se puede hacer uso del siguiente comando para instalarlo:

```bash
sudo apt install python3
```
Para verificar la versión de Python instalada, se puede ejecutar el siguiente comando:
```bash
python3 --version
```

## Creación de un entorno virtual
Para evitar conflictos entre las dependencias de diferentes proyectos, es recomendable crear un entorno virtual para el proyecto. Esto se puede hacer con el siguiente comando:
```bash
python3 -m venv <nombre del entorno, normalmente se usa venv o env>
```
Para activar el entorno virtual, se puede usar el siguiente comando:
```bash
source <nombre del entorno>/bin/activate
```

## Instalación de PLY
Primero verificar que se tiene pip instalado, para ello se puede ejecutar el siguiente comando:
```bash
pip --version
```
Ahora, para instalar PLY, se puede usar el siguiente comando:
```bash
pip install ply
```
Si queremos dejar registro de las librerías instaladas en el proyecto, podemos generar un archivo requirements.txt con el siguiente comando:
```bash
pip freeze > requirements.txt
```
Y luego para instalar las librerías desde el archivo requirements.txt, se puede usar el siguiente comando:
```bash
pip install -r requirements.txt
```
Siempre desde el entorno virtual activado, para evitar conflictos con otras librerías instaladas en el sistema.
Para desactivar el entorno virtual, se puede usar el siguiente comando:
```bash
deactivate
```

Puedes revisar el ejemplo en `ejemplo/`, revisa el archivo `ejemplo/calclex.py` para observar la implementación del analizador léxico y `ejemplo/main.py` para observar la implementación del analizador sintáctico. Para correr el ejemplo, primero asegúrate de tener el entorno virtual activado e instalar las dependencias, luego ejecuta el siguiente comando:
```bash
python ejemplo/main.py
```