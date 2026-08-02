from flask import Flask, render_template, request, jsonify

from myparser import parser
from AST.Visitor.typechecker import TypeChecker
from AST.Visitor.interpreter import Interpreter

from contextlib import redirect_stdout
from io import StringIO


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/compile")
def compile():

    code = request.json["code"]

    response = {
        "errors": [],
        "output": []
    }

    try:

        ast = parser.parse(code)

        checker = TypeChecker()

        for node in ast:
            node.visit(checker)


        if checker.errors:
            response["errors"] = checker.errors
            return jsonify(response)


        interpreter = Interpreter()

        output = StringIO()

        with redirect_stdout(output):
            for node in ast:
                node.visit(interpreter)


        response["output"] = output.getvalue().splitlines()


    except Exception as e:
        response["errors"].append(str(e))


    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)