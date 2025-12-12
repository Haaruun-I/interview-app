#!/usr/bin/env python3
"""Simple Flask API exposing an equation solver."""

from __future__ import annotations
import os

from tokenize import TokenError
from sympy import solve as solveExpression
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
from flask import Flask, jsonify, request

parseExpression = lambda equation: parse_expr(equation,
                transformations=(standard_transformations + (implicit_multiplication_application, convert_xor)))

stringifyExpression = lambda expression: str(expression).replace("**", "^")

def solveEquation(inputEquation: str) -> tuple[str, list[str]]:
    # `parse_expr` does not allow equal signs in expressions
    # this just turns equations in the form `x = y` into `x - y` where =0 is implied
    if "=" in inputEquation:
        parts = inputEquation.split("=")
        if len(parts) > 2: raise SyntaxError()
        
        expression = parseExpression(parts[0]) - parseExpression(parts[1])
    else:
        expression = parseExpression(inputEquation)

    solutions = []
    for symbol in expression.free_symbols:
        solutionsForSymbol = solveExpression(expression, symbol)
        for solution in solutionsForSymbol:
            solutions.append(str(symbol) + " = " + stringifyExpression(solution))

    return stringifyExpression(expression) + " = 0", solutions

def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):  # type: ignore[override]
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.get("/solve")
    def solve():
        equation = (request.args.get("equation") or "").strip()
        if not equation:
            return jsonify({"error": "Missing 'equation' query parameter"}), 400

        try:
            parsedEquation, solutions = solveEquation(equation)
        except (SyntaxError, TokenError) as e:
            return jsonify({"error": "Syntax Error"}), 400

        return jsonify({"result": {"equation": parsedEquation, "solutions": solutions}})


    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"message": "Equation API. Try /solve?equation=1+1"})

    return app


def run() -> None:
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)

    return expression, solution

if __name__ == "__main__":
    run()
