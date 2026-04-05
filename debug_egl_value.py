from egl_interpreter import EGLValue
def test():
    v = EGLValue(0)
    v1 = v + 1
    print(f"0 + 1 = {v1.val}")
    v2 = v1 + 1
    print(f"1 + 1 = {v2.val}")

test()
