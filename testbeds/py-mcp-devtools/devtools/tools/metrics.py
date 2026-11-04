"""Small calculations over metric samples, for capacity questions."""

import ast
import math
import operator
import statistics

from devtools.app import mcp

SAFE_NAMES = {"min": min, "max": max, "mean": statistics.fmean, "p95": None, "sqrt": math.sqrt}

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


SAFE_NAMES["p95"] = _p95


@mcp.tool()
def evaluate(expression: str, samples: list[float]) -> float:
    """Evaluate a formula over the samples, e.g. "p95(x) / mean(x)"."""
    namespace = dict(SAFE_NAMES, x=samples)
    return float(eval(expression, {"__builtins__": {}}, namespace))


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    raise ValueError("only numbers and + - * / are allowed")


@mcp.tool()
def arithmetic(expression: str) -> float:
    """Plain arithmetic, parsed without eval."""
    return _eval_node(ast.parse(expression, mode="eval").body)
