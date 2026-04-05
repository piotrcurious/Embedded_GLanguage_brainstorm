#include <EGL.h>

// Sprite Game Mock Sketch
int px = 200, py = 150;

void setup() {
  EGL.init(400, 300, "black");
  // Pre-define player sprite
  EGL.runCmd("P", "player, 20, 20");
  EGL.runCmd("F", "green");
  EGL.runCmd("BX", "0, 0, 20, 20");
  EGL.runCmd("P", "main");
}

void loop() {
  if (EGL.available()) {
    char key = EGL.readKey();
    if (key == 'w') py -= 5;
    if (key == 's') py += 5;
    if (key == 'a') px -= 5;
    if (key == 'd') px += 5;
  }

  EGL.setVar("$px", px);
  EGL.setVar("$py", py);
  EGL.flip();
}
