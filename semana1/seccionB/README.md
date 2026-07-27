# Guía de Entornos Virtuales (venv) en Python

Organización de Lenguajes y Compiladores 2 — Sección B
Material de apoyo para el desarrollo del Proyecto 1 (OxigenScript con PLY)

---

## 1. ¿Qué es un entorno virtual y por qué lo necesitamos?

Cuando instalas una librería con `pip install`, por defecto se instala **globalmente** en tu sistema. Esto genera problemas:

- Si dos proyectos necesitan versiones distintas de la misma librería (por ejemplo, PLY 3.9 vs PLY 3.11), van a chocar.
- Instalar cosas globalmente puede interferir con paquetes que el sistema operativo (Linux) usa internamente.
- El proyecto no es **reproducible**: si el auxiliar o un compañero clona tu repositorio, no sabe exactamente qué versiones de librerías necesita instalar.

Un **entorno virtual** es una carpeta aislada con su propia copia del intérprete de Python y sus propias librerías, separada del resto del sistema. Cada proyecto tiene el suyo.

---

## 2. Crear un entorno virtual

Dentro de la carpeta de tu proyecto:

```bash
python3 -m venv venv
```

Esto crea una carpeta `venv/` con una copia del intérprete de Python. El nombre `venv` es una convención, pero puedes llamarla como quieras (otra convención común es `.venv`).

---

## 3. Activar el entorno virtual

```bash
# Linux / macOS
source venv/bin/activate
```

Cuando está activo, verás el nombre del entorno entre paréntesis al inicio de la terminal:

```bash
(venv) usuario@maquina:~/proyecto$
```

Mientras esté activo, cualquier `pip install` o `python` que ejecutes usa **esa copia aislada**, no la del sistema operativo.

---

## 4. Instalar dependencias dentro del entorno

Con el entorno activado:

```bash
pip install ply
pip install django   # o el framework que usen para la GUI
```

---

## 5. Congelar y restaurar dependencias

Esto es clave para que el proyecto sea reproducible y para el entregable en GitHub.

**Guardar las dependencias instaladas:**

```bash
pip freeze > requirements.txt
```

**Instalar exactamente las mismas dependencias en otra máquina (o para el auxiliar/evaluador):**

```bash
pip install -r requirements.txt
```

Recomendación: corran `pip freeze > requirements.txt` cada vez que instalen una librería nueva, y suban ese archivo actualizado a su commit.

---

## 6. Desactivar el entorno

```bash
deactivate
```

---

## 7. Qué SÍ y qué NO subir a Git

**NO se sube a Git** (agregar a `.gitignore`):

```
venv/
__pycache__/
*.pyc
parser.out
parsetab.py
```

- `venv/` es específica de cada máquina, no debe compartirse.
- `parser.out` y `parsetab.py` son archivos que PLY genera automáticamente al construir el parser; no son parte del código fuente.

**SÍ se sube a Git:**

- `requirements.txt`
- Todo el código fuente (`.py`)
- Documentación (README, manual de usuario, diagramas)

---

## 8. Flujo completo de trabajo (resumen)

```bash
mkdir mi_proyecto
cd mi_proyecto

python3 -m venv venv
source venv/bin/activate

pip install ply django

# ... crear archivos .py, avanzar en el proyecto ...

pip freeze > requirements.txt

git init
git add .
git commit -m "Estructura inicial del proyecto"
```

---

## 9. Errores comunes

| Problema | Causa probable | Solución |
|---|---|---|
| `venv: command not found` | Python no está instalado o no está en el PATH | Verificar con `python3 --version` |
| Al activar no aparece `(venv)` en la terminal | Se activó mal la ruta según el sistema operativo | Revisar sección 3 según tu SO |
| `pip install` instala en el sistema global, no en el venv | El entorno no estaba activado | Confirmar que aparezca `(venv)` antes de instalar |
| Compañeros no pueden correr el proyecto | Falta `requirements.txt` o está desactualizado | Regenerar con `pip freeze > requirements.txt` y subirlo |

---

## 10. Verificar que estás dentro del entorno correcto

```bash
which python      # Linux/macOS
where python       # Windows

pip list           # muestra solo las librerías instaladas en el entorno activo
```

Si `which python` apunta a la carpeta `venv/`, están trabajando en el entorno correcto.