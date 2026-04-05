#include <EGL.h>

// Sensor Dashboard Sketch
void setup() {
  EGL.init(400, 300, "black");
}

void loop() {
  int temp = analogRead(A0); // 0-1023
  int pressure = analogRead(A1);

  // Inject values into EGL variables
  EGL.setVar("$temp", temp);
  EGL.setVar("$press", pressure);

  EGL.flip();
  delay(100);
}
