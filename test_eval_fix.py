from egl_interpreter import EGLInterpreter

it = EGLInterpreter()
it.set_var("$count", 1)
expr = '"Count: " + $count'
res = it.eval_expr(expr)
print(f"Expr: {expr} -> {res} (type: {type(res)})")

# Test literal string in eval without variable
expr2 = '"Hello " + "World"'
res2 = it.eval_expr(expr2)
print(f"Expr: {expr2} -> {res2} (type: {type(res2)})")

# Test addition of strings in EGL format
it.set_var("$s1", "A")
it.set_var("$s2", "B")
expr3 = "$s1 + $s2"
res3 = it.eval_expr(expr3)
print(f"Expr: {expr3} -> {res3} (type: {type(res3)})")
