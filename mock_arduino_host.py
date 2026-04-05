import sys
import re
from egl_interpreter import EGLInterpreter

# Simulated EGL Library for "Arduino"
class EGL_Lib:
    def __init__(self, host):
        self.host = host
    def init(self, w, h, bg):
        self.host.run_cmd('S', [w, h, bg])
    def clear(self, bg):
        self.host.run_cmd('F', [bg])
        # Get dimensions from image
        img = self.host.interpreter.images["main"]
        self.host.run_cmd('BX', [0, 0, img.width, img.height])
    def drawString(self, x, y, text):
        self.host.run_cmd('M', [x, y])
        self.host.run_cmd('T', [text])
    def flip(self):
        self.host.run_cmd('FB', [])
    def available(self):
        return len(self.host.interpreter.serial_in) > 0
    def readKey(self):
        if self.available():
            return self.host.interpreter.serial_in.pop(0)
        return None

class MockArduinoEnvironment:
    def __init__(self):
        self.interpreter = EGLInterpreter()
        self.egl_lib = EGL_Lib(self)
        self.buffer = ""
        self.cursor = 0

    def run_cmd(self, cmd, args):
        self.interpreter.run_cmd(cmd, args)

    # The "Sketch" Logic
    def setup(self):
        self.egl_lib.init(400, 300, "white")
        self.egl_lib.drawString(10, 10, "ARDUINO TEXT EDITOR")
        self.egl_lib.flip()

    def loop(self, key_event=None):
        if key_event:
            self.interpreter.serial_in.append(key_event)

        if self.egl_lib.available():
            key = self.egl_lib.readKey()
            if key == 'BACKSPACE' or key == '\b':
                if len(self.buffer) > 0:
                    self.buffer = self.buffer[:-1]
            else:
                self.buffer += str(key)

            # Redraw
            self.egl_lib.clear("white")
            self.run_cmd('K', ["black"])
            self.egl_lib.drawString(10, 10, "ARDUINO TEXT EDITOR")
            self.run_cmd('K', ["blue"])
            self.egl_lib.drawString(10, 50, "Buffer: " + self.buffer)
            self.egl_lib.flip()

if __name__ == "__main__":
    env = MockArduinoEnvironment()
    env.setup()
    # Simulate typing "EGL"
    env.loop("E")
    env.loop("G")
    env.loop("L")
    env.loop("!")

    if env.interpreter.front_buffer:
        env.interpreter.front_buffer.save("arduino_mock_output.png")
        print("Saved arduino_mock_output.png")
    print("Done.")
