from myparser import parser
from AST.typechecker import TypeChecker

if __name__ == "__main__":    
    while True:
        try:
            s = input('calc > ')
        except EOFError:
            break
        if not s:
            continue
        result = parser.parse(s)
        type_checker = TypeChecker()
        for node in result:
            try:                
                result = node.visit(type_checker)
                print(f"Type: {result}")
            except Exception as e:
                print(f"Error: {e}")