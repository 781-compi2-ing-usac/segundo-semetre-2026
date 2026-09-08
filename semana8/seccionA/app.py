from flask import Flask, render_template, request, jsonify
from io import StringIO
from contextlib import redirect_stdout

from myparser import parser
from AST.Visitor.typechecker import TypeChecker
from AST.Visitor.compiler import Compiler
from AST.Visitor.interpreter import Interpreter
from AST.Builder.tac_builder import TACBuilder
from AST.Builder.arm_builder import ARMBuilder
from AST.errors import CompilerError, ParseError


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/compile")
def compile():

    code = request.json["code"]
    mode = request.json.get("mode", "interpreter")
    builder_type = request.json.get("builder", "tac")

    response = {"errors": [], "output": []}

    try:
        ast = parser.parse(code)

    except ParseError as e:
        response["errors"].append(e.to_dict())
        return jsonify(response)

    except Exception as e:
        response["errors"].append({"phase": "parse", "message": str(e)})
        return jsonify(response)

    try:
        checker = TypeChecker()

        for node in ast:
            checker.dispatch(node)

        if checker.errors:
            response["errors"] = [e.to_dict() for e in checker.errors]
            return jsonify(response)        

    except CompilerError as e:
        response["errors"].append(e.to_dict())
        return jsonify(response)

    except Exception as e:
        response["errors"].append({"phase": "typecheck", "message": str(e)})
        return jsonify(response)

    try:
        if mode == "compiler":
            if builder_type == "arm":
                builder = ARMBuilder()
            else:
                builder = TACBuilder()
            
            compiler = Compiler(builder)

            for node in ast:
                compiler.dispatch(node)

            if compiler.errors:
                response["errors"] = [e.to_dict() for e in compiler.errors]
                return jsonify(response)

            generated_code = compiler.get_code()
            response["output"] = [generated_code]
        
        else:
            interpreter = Interpreter()
            
            output_buffer = StringIO()
            with redirect_stdout(output_buffer):
                for node in ast:
                    interpreter.dispatch(node)
            
            if interpreter.errors:
                response["errors"] = [e.to_dict() for e in interpreter.errors]
                return jsonify(response)
            
            output = output_buffer.getvalue()
            response["output"] = output.strip().split("\n") if output.strip() else []

    except CompilerError as e:
        response["errors"].append(e.to_dict())

    except Exception as e:
        response["errors"].append({"phase": mode, "message": str(e)})

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
