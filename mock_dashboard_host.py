from mock_arduino_base import MockArduinoBase

class DashboardMock(MockArduinoBase):
    def setup(self):
        self.egl.init(400, 300, "black")

    def loop(self):
        # Simulate sensor readings
        self.egl.set_var("$temp", 850)
        self.egl.set_var("$press", 420)
        self.egl.flip()

if __name__ == "__main__":
    mock = DashboardMock("demo_dashboard.egl")
    mock.run_simulation(iterations=1, output_name="dashboard_output.png")
