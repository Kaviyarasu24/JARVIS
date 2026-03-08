from __future__ import annotations

import ast
import operator
import re
from typing import Union

Number = Union[int, float]

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def normalize_expression(raw_expression: str) -> str:
    """Convert common spoken math words into a Python-style expression."""
    expr = raw_expression.lower().strip()

    replacements = [
        ("multiplied by", "*"),
        ("times", "*"),
        ("x", "*"),
        ("plus", "+"),
        ("minus", "-"),
        ("divided by", "/"),
        ("over", "/"),
        ("modulus", "%"),
        ("mod", "%"),
        ("to the power of", "**"),
        ("power", "**"),
        ("open bracket", "("),
        ("close bracket", ")"),
        ("open parenthesis", "("),
        ("close parenthesis", ")"),
    ]

    for src, target in replacements:
        expr = expr.replace(src, target)

    # Keep only safe calculator characters after normalization.
    expr = re.sub(r"[^0-9\s\+\-\*/\(\)\.%]", "", expr)
    expr = re.sub(r"\s+", "", expr)
    return expr


def _eval_ast(node: ast.AST) -> Number:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed.")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        value = _eval_ast(node.operand)
        return _ALLOWED_OPERATORS[type(node.op)](value)
    raise ValueError("Unsupported expression.")


def calculate_text(raw_expression: str) -> str:
    """Evaluate spoken math safely and return a spoken response."""
    expression = normalize_expression(raw_expression)
    if not expression:
        return "Please provide a valid math expression."

    try:
        parsed = ast.parse(expression, mode="eval")
        result = _eval_ast(parsed)
    except ZeroDivisionError:
        return "Division by zero is not allowed."
    except Exception:
        return "I could not calculate that expression."

    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return f"The answer is {result}."
