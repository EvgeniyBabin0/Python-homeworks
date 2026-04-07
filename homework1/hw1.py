from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ast
import operator

app = FastAPI(title="Calculator API")

current_expression = ""


class BinaryOperation(BaseModel):
    a: float
    op: str
    b: float


class ExpressionInput(BaseModel):
    expression: str


OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


@app.get("/")
def root():
    return {"message": "Calculator API is running"}


@app.get("/add")
def add(a: float, b: float):
    return {"expression": f"{a} + {b}", "result": a + b}


@app.get("/sub")
def sub(a: float, b: float):
    return {"expression": f"{a} - {b}", "result": a - b}


@app.get("/mul")
def mul(a: float, b: float):
    return {"expression": f"{a} * {b}", "result": a * b}


@app.get("/div")
def div(a: float, b: float):
    if b == 0:
        raise HTTPException(status_code=400, detail="Деление на ноль запрещено")
    return {"expression": f"{a} / {b}", "result": a / b}


@app.post("/expression/create")
def create_expression(data: BinaryOperation):
    global current_expression

    if data.op not in OPERATORS:
        raise HTTPException(status_code=400, detail="Поддерживаются только операции +, -, *, /")

    current_expression = f"({data.a} {data.op} {data.b})"
    return {"current_expression": current_expression}


def safe_eval(expression: str):
    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)

        if isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)

            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise HTTPException(status_code=400, detail="Деление на ноль запрещено")
                return left / right

            raise HTTPException(status_code=400, detail="Недопустимая операция")

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -eval_node(node.operand)

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        raise HTTPException(status_code=400, detail="Некорректное выражение")

    try:
        tree = ast.parse(expression, mode="eval")
        return eval_node(tree)
    except SyntaxError:
        raise HTTPException(status_code=400, detail="Ошибка синтаксиса в выражении")


@app.post("/expression/set")
def set_expression(data: ExpressionInput):
    global current_expression
    current_expression = data.expression
    return {"current_expression": current_expression}


@app.get("/expression/current")
def get_current_expression():
    return {"current_expression": current_expression}


@app.post("/expression/execute")
def execute_current_expression():
    if not current_expression:
        raise HTTPException(status_code=400, detail="Текущее выражение не задано")

    result = safe_eval(current_expression)
    return {
        "expression": current_expression,
        "result": result
    }


@app.post("/expression/evaluate")
def evaluate_expression(data: ExpressionInput):
    result = safe_eval(data.expression)
    return {
        "expression": data.expression,
        "result": result
    }