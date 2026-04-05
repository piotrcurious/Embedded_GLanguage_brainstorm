from mock_arduino_base import MockArduinoBase

class MenuMock(MockArduinoBase):
    def setup(self):
        self.selection = 0
        self.egl.init(400, 300, "white")

    def loop(self):
        # Process EGL's serial output to update host state
        for msg in self.interpreter.serial_out:
            if "SELECTED:" in msg:
                self.selection = int(msg.split(":")[1].strip('"'))
        self.interpreter.serial_out = []

        self.egl.set_var("$sel", self.selection)
        self.egl.flip()

if __name__ == "__main__":
    mock = MenuMock("demo_menu.egl")
    # Simulate a click on the second menu item
    mock.interpreter.event_queue.append(('MC', 75, 125, 1))
    # Run two iterations so the second can render the update from the first's serial msg
    mock.run_simulation(iterations=2, output_name="menu_output.png")
