#!/usr/bin/env python3
"""Script de prueba para generar código LLVM y ARM desde el compilador"""

import sys
import os

# Agregar el directorio actual al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from myparser import parser
from AST.Visitor.typechecker import TypeChecker
from AST.Visitor.compiler import Compiler
from AST.Builder.tac_builder import TACBuilder
from AST.Builder.arm_builder import ARMBuilder


def generate_and_save(code: str, name: str):
    """Genera código LLVM y ARM para el código dado y lo guarda en archivos"""
    print(f"\n{'=' * 60}")
    print(f"Probando: {name}")
    print(f"{'=' * 60}")
    print(f"Código fuente:\n{code}\n")

    # Parsear
    try:
        ast = parser.parse(code)
    except Exception as e:
        print(f"❌ Error de parseo: {e}")
        return False

    # Typecheck
    checker = TypeChecker()
    for node in ast:
        checker.dispatch(node)

    if checker.errors:
        print(f"❌ Errores de tipo:")
        for err in checker.errors:
            print(f"   {err}")
        return False

    print("✅ Typecheck OK")

    # Generar LLVM IR
    try:
        tac_builder = TACBuilder()
        tac_compiler = Compiler(tac_builder)
        for node in ast:
            tac_compiler.dispatch(node)

        llvm_code = tac_compiler.get_code()
        llvm_file = f"LLVM/{name}.ll"
        with open(llvm_file, "w") as f:
            f.write(llvm_code)
        print(f"✅ LLVM IR generado: {llvm_file}")
    except Exception as e:
        print(f"❌ Error generando LLVM: {e}")
        return False

    # Generar ARM64
    try:
        arm_builder = ARMBuilder()
        arm_compiler = Compiler(arm_builder)
        for node in ast:
            arm_compiler.dispatch(node)

        arm_code = arm_compiler.get_code()
        arm_file = f"ARM/{name}.asm"
        with open(arm_file, "w") as f:
            f.write(arm_code)
        print(f"✅ ARM64 generado: {arm_file}")
    except Exception as e:
        print(f"❌ Error generando ARM: {e}")
        return False

    return True


def main():
    # Tests básicos
    tests = [
        (
            "test1_arithmetic",
            """
int x = 10
int y = 5
print(x + y)
print(x - y)
print(x * y)
""",
        ),
        (
            "test2_if_simple",
            """
int x = 10
if (x < 15) {
    print(x)
}
""",
        ),
        (
            "test3_if_and",
            """
int x = 10
int y = 5
if (x < 15 & y > 3) {
    print(x + y)
}
""",
        ),
        (
            "test4_if_or",
            """
int x = 10
if (x < 5 | x > 8) {
    print(x)
}
""",
        ),
        (
            "test5_while_simple",
            """
int x = 5
while (x > 0) {
    print(x)
    x = x - 1
}
""",
        ),
        (
            "test6_while_and",
            """
int x = 10
int y = 5
while (x > 0 & y > 0) {
    print(x)
    x = x - 1
    y = y - 1
}
""",
        ),
        (
            "test7_bool_materialization",
            """
int x = 10
bool a = x < 15
bool b = x > 5 & x < 20
print(a)
print(b)
""",
        ),
        (
            "test8_complex_condition",
            """
int x = 10
int y = 5
if (x > 5 & y < 10 | x == 10) {
    print(x + y)
}
""",
        ),
        (
            "test9_array_1d",
            """
int arr = [1, 2, 3, 4, 5]
print(arr[0])
print(arr[2])
print(arr[4])
""",
        ),
        (
            "test10_array_2d",
            """
int matrix = [[1, 2, 3], [4, 5, 6]]
print(matrix[0][0])
print(matrix[0][2])
print(matrix[1][1])
""",
        ),
        (
            "test11_array_assign_1d",
            """
int arr = [1, 2, 3, 4, 5]
arr[0] = 10
arr[2] = 30
arr[4] = 50
print(arr[0])
print(arr[2])
print(arr[4])
""",
        ),
        (
            "test12_array_assign_2d",
            """
int matrix = [[1, 2, 3], [4, 5, 6]]
matrix[0][0] = 100
matrix[0][2] = 300
matrix[1][1] = 500
print(matrix[0][0])
print(matrix[0][2])
print(matrix[1][1])
""",
        ),
        (
            "test13_array_3d",
            """
int cube = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
print(cube[0][0][0])
print(cube[0][1][1])
print(cube[1][0][0])
print(cube[1][1][1])
""",
        ),
    ]

    success_count = 0
    for name, code in tests:
        if generate_and_save(code, name):
            success_count += 1

    print(f"\n{'=' * 60}")
    print(f"Resumen: {success_count}/{len(tests)} tests generaron código correctamente")
    print(f"{'=' * 60}")

    if success_count == len(tests):
        print("\n✅ Todos los tests pasaron la generación de código")
        print("\nAhora ejecuta los scripts de build:")
        print("  cd LLVM && ./build.sh test1_arithmetic.ll")
        print("  cd ARM && ./build.sh test1_arithmetic.asm")
    else:
        print(f"\n❌ {len(tests) - success_count} tests fallaron")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
