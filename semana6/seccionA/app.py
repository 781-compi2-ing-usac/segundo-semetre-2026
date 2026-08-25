from flask import Flask, render_template, request, jsonify

from myparser import parser
from AST.Visitor.typechecker import TypeChecker
from AST.Visitor.interpreter import Interpreter
from AST.errors import CompilerError, ParseError

from contextlib import redirect_stdout
from io import StringIO


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

        interpreter = Interpreter()

        output = StringIO()

        with redirect_stdout(output):
            for node in ast:
                interpreter.dispatch(node)

        if interpreter.errors:
            response["errors"] = [e.to_dict() for e in interpreter.errors]
            return jsonify(response)

        response["output"] = output.getvalue().splitlines()

    except CompilerError as e:
        response["errors"].append(e.to_dict())

    except Exception as e:
        response["errors"].append({"phase": "unknown", "message": str(e)})

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
