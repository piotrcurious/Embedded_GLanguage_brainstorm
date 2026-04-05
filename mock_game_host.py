from mock_arduino_base import MockArduinoBase

class GameMock(MockArduinoBase):
    def setup(self):
        self.px, self.py = 200, 150
        self.egl.init(400, 300, "black")
        self.egl.run_cmd('P', ["player", 20, 20])
        self.egl.run_cmd('F', ["green"])
        self.egl.run_cmd('BX', [0, 0, 20, 20])
        self.egl.run_cmd('P', ["main"])

    def loop(self):
        # Simulate moving 'd' then 's'
        for key in ['d', 'd', 'd', 's', 's']:
            if key == 'w': self.py -= 5
            if key == 's': self.py += 5
            if key == 'a': self.px -= 5
            if key == 'd': self.px += 5

        self.egl.set_var("$px", self.px)
        self.egl.set_var("$py", self.py)
        self.egl.flip()

if __name__ == "__main__":
    mock = GameMock("demo_game.egl")
    mock.run_simulation(iterations=1, output_name="game_output.png")
