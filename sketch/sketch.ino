#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

Arduino_LED_Matrix matrix;

bool showFrame(String columns) {
  if (columns.length() != 26) return false;
  uint8_t pixels[104] = {};
  for (int x = 0; x < 13; ++x) {
    uint8_t bits = 0;
    for (int digit = 0; digit < 2; ++digit) {
      char c = columns[2 * x + digit];
      if (c >= '0' && c <= '9') bits = bits * 16 + c - '0';
      else if (c >= 'a' && c <= 'f') bits = bits * 16 + c - 'a' + 10;
      else return false;
    }
    for (int y = 0; y < 8; ++y) pixels[y * 13 + x] = (bits >> y) & 1;
  }
  matrix.draw(pixels);
  return true;
}

void setup() {
  matrix.begin();
  matrix.setGrayscaleBits(1);
  showFrame("00000000000000000000000000");
  Bridge.begin();
  Bridge.provide("bloop_frame", showFrame);
}

void loop() {}
