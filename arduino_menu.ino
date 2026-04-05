#include <EGL.h>

// Interactive Menu Sketch
int selection = 0;

void setup() {
  EGL.init(400, 300, "white");
}

void loop() {
  // Listen for menu selection changes via Serial (from EGL script)
  if (Serial.available()) {
    String msg = Serial.readString();
    if (msg.indexOf("SELECTED:") != -1) {
       selection = msg.substring(9).toInt();
    }
  }

  EGL.setVar("$sel", selection);
  EGL.flip();
}
