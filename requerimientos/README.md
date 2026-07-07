# Instalación de Requerimientos para el Proyecto

Antes de todo esto, recordemos que el proyecto será desarrollado en un sistema operativo Linux, por lo que se recomienda las distribuciones basadas en Debian, como Ubuntu o Linux Mint. En última instacia, se puede hacer uso de WSL (Windows Subsystem for Linux) en caso de que se esté trabajando en un sistema operativo Windows.

## Requerimientos
- C# y .NET SDK
- Java JDK
- ANTLR4

### Instalación de C# y .NET SDK

Para instalar C# y .NET SDK, se puede seguir los siguientes pasos:
1. Debemos ir a nuestra carpeta descargas ~/Downloads:
```bash
cd ~/Downloads
```
2. Descargar el instalador de .NET SDK desde la página oficial de Microsoft:
```bash
curl -L https://dot.net/v1/dotnet-install.sh -o dotnet-install.sh
```
3. Dar permisos de ejecución al instalador:
```bash
chmod +x dotnet-install.sh
```
4. Ejecutar el instalador:
```bash
./dotnet-install.sh --channel LTS
```
5. Agregar la ruta de instalación a la variable de entorno PATH:
```bash
# Agregar las siguientes líneas al final del archivo ~/.bashrc o ~/.zshrc, dependiendo del shell que se esté utilizando:
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
```
6. Actualizar la terminal para que los cambios surtan efecto:
```bash
source ~/.bashrc
```
7. Verificar la instalación de .NET SDK:
```bash
dotnet --version
```

### Instalación de Java JDK
Java es necesario para instalar las tools de ANTLR4. Para instalar Java JDK, se pueden seguir los siguientes pasos:
1. Abrir una terminal y actualizar los repositorios:
```bash
sudo apt update
```
2. Instalar Java JDK:
```bash
sudo apt install openjdk-11-jdk
```
>[!NOTE]
> Según la documentación oficial de ANTLR4, se recomienda usar Java 11 o una versión posterior.
3. Verificar la instalación de Java:
```bash
java -version
```

### Instalación de ANTLR4
ANTLR4 es una herramienta para generar analizadores léxicos y sintácticos. Para instalar ANTLR4, se pueden seguir los siguientes pasos:
1. Descargar el archivo JAR de ANTLR4 desde la página oficial:
```bash
cd /usr/local/lib
curl -O https://www.antlr.org/download/antlr-4.13.2-complete.jar
```
2. Agregar la ruta de ANTLR4 a la variable de entorno CLASSPATH:
```bash
# Agregar las siguientes líneas al final del archivo ~/.bashrc o ~/.zshrc, dependiendo del shell que se esté utilizando:
export CLASSPATH=".:/usr/local/lib/antlr-4.13.2-complete.jar:$CLASSPATH"
# Agregar alias para facilitar el uso de ANTLR4:
alias antlr4='java -Xmx500M -cp "/usr/local/lib/antlr-4.13.2-complete.jar:$CLASSPATH" org.antlr.v4.Tool'
alias grun='java -Xmx500M -cp "/usr/local/lib/antlr-4.13.2-complete.jar:$CLASSPATH" org.antlr.v4.gui.TestRig'
```
3. Actualizar la terminal para que los cambios surtan efecto:
```bash
source ~/.bashrc
```
4. Verificar la instalación de ANTLR4:
```bash
antlr4
```

>[!NOTE]
> Si en dado caso, estas usando un agente de IA, ten en cuenta que los alias de ANTLR4 y grun no funcionarán ya que para el agente de IA no se puede modificar el archivo ~/.bashrc o ~/.zshrc. Para arreglarlo le podrías indicar al agente de IA que ejecute los comandos completos de ANTLR4 y grun, en lugar de usar los alias.

## Crear un proyecto de ejemplo con dotnet
Para crear un proyecto de ejemplo con dotnet, se pueden seguir los siguientes pasos:
1. Crear un nuevo proyecto de consola:
```bash
dotnet new console -n MiCompilador
```
2. Cambiar al directorio del proyecto:
```bash
cd MiCompilador
```
3. Instalar el paquete de ANTLR4 para C#:
```bash
dotnet add package Antlr4.Runtime.Standard --version 4.13.1
```
4. Crear un archivo de gramática ANTLR4 (por ejemplo, `MiGramatica.g4`) en el directorio del proyecto y agregar la gramática deseada.
```bash
nano MiGramatica.g4
```
5. Escribiremos una gramática simple para un lenguaje de ejemplo. Por ejemplo:
```antlr
grammar MiGramatica;

prog:   stat+ ;

stat:   expr NEWLINE;

expr:   expr ('*'|'/') expr
    |   expr ('+'|'-') expr
    |   INT
    |   '(' expr ')'
    ;

NEWLINE : [\r\n]+ ;
INT     : [0-9]+ ;
WS      : [ \t]+ -> skip ;
```
6. Generar el código fuente de C# a partir de la gramática ANTLR4:
```bash
antlr4 -Dlanguage=CSharp -visitor MiGramatica.g4 -o Grammar
```
7. En `MiCompilador/`, tienes un proyecto de ejemplo que utiliza ANTLR4 para analizar expresiones aritméticas simples. Puedes copiar el contenido de `MiCompilador/Program.cs` y `MiCompilador/EvalVisitor.cs` a tu proyecto para probarlo. Lo demás se genera con los comandos anteriores.


### Bibliografía
- [Documentación oficial de .NET](https://learn.microsoft.com/en-us/dotnet/core/install/linux-scripted-manual#scripted-install)
- [Documentación oficial de ANTLR4](https://github.com/antlr/antlr4/blob/master/doc/getting-started.md)