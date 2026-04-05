#include <EGL.h>

// Simple Arduino Text Editor Mock
char buffer[100];
int cursor = 0;

void setup() {
  Serial.begin(115200);
  EGL.init(800, 600, "white");
  EGL.drawString(10, 10, "EGL ARDUINO EDITOR v1.0");
  EGL.flip();
}

void loop() {
  if (EGL.available()) {
    char key = EGL.readKey();
    if (key == '\b' && cursor > 0) {
      cursor--;
      buffer[cursor] = '\0';
    } else if (cursor < 99) {
      buffer[cursor] = key;
      cursor++;
      buffer[cursor] = '\0';
    }

    // Refresh display
    EGL.clear("white");
    EGL.drawString(10, 10, "EGL ARDUINO EDITOR v1.0");
    EGL.drawString(10, 50, buffer);
    EGL.flip();
  }
}
