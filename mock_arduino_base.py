from egl_interpreter import EGLInterpreter

class EGL_Lib:
    def __init__(self, host):
        self.host = host
    def init(self, w, h, bg):
        self.host.interpreter.run_cmd('S', [w, h, bg])
    def clear(self, bg):
        self.host.interpreter.run_cmd('F', [bg])
        img = self.host.interpreter.images["main"]
        self.host.interpreter.run_cmd('BX', [0, 0, img.width, img.height])
    def drawString(self, x, y, text):
        self.host.interpreter.run_cmd('M', [x, y])
        self.host.interpreter.run_cmd('T', [text])
    def flip(self):
        self.host.interpreter.run_cmd('FB', [])
    def available(self):
        return len(self.host.interpreter.serial_in) > 0
    def readKey(self):
        if self.available(): return self.host.interpreter.serial_in.pop(0)
        return None
    def run_cmd(self, cmd, args):
        self.host.interpreter.run_cmd(cmd, args)
    def set_var(self, name, val):
        self.host.interpreter.set_var(name, val)

class MockArduinoBase:
    def __init__(self, egl_script):
        self.interpreter = EGLInterpreter()
        self.egl = EGL_Lib(self)
        self.egl_script = egl_script
        with open(egl_script, 'r') as f: self.code = f.read()

    def setup(self): pass
    def loop(self): pass

    def run_simulation(self, iterations=1, output_name="output.png"):
        self.setup()
        for _ in range(iterations):
            # Process events first if they were injected externally
            self.interpreter.run_code(self.code)
            self.loop()

        out_img = self.interpreter.front_buffer if self.interpreter.front_buffer else self.interpreter.images.get("main")
        if out_img:
            out_img.save(output_name)
            print(f"Saved {output_name}")
