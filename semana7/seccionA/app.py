from flask import Flask, render_template, request, jsonify

from myparser import parser
from AST.Visitor.typechecker import TypeChecker
from AST.Visitor.compiler import Compiler
from AST.Builder.tac_builder import TACBuilder
from AST.errors import CompilerError, ParseError


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/compile")
def compile():

    code = request.json["code"]

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
        builder = TACBuilder()
        compiler = Compiler(builder)

        for node in ast:
            compiler.dispatch(node)

        if compiler.errors:
            response["errors"] = [e.to_dict() for e in compiler.errors]
            return jsonify(response)

        llvm_ir = compiler.get_code()
        response["output"] = [llvm_ir]

    except CompilerError as e:
        response["errors"].append(e.to_dict())

    except Exception as e:
        response["errors"].append({"phase": "compile", "message": str(e)})

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
