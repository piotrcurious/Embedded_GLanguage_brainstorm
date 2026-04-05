from egl_interpreter import EGLInterpreter

it = EGLInterpreter()
it.set_var("$text_buffer", "HELLO")
expr = '"Text: " + $text_buffer'
res = it.eval_expr(expr)
print(f"Expr: {expr} -> {res} (type: {type(res)})")

it.set_var("$disp", res)
expr2 = '$disp'
res2 = it.eval_expr(expr2)
print(f"Expr: {expr2} -> {res2} (type: {type(res2)})")
