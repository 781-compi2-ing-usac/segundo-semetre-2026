from lexer import lexer
from parser import parser


def main():
    print("Calculadora mínima (Ctrl+C para salir)\n")

    while True:
        try:
            data = input('calc> ')
        except (EOFError, KeyboardInterrupt):
            break

        if not data:
            continue

        resultado = parser.parse(data, lexer=lexer)
        print(resultado)


if __name__ == '__main__':
    main()