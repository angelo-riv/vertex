#include <Wire.h>

void setup() {
  Serial.begin(115200);
  Wire.begin(21,22);

  Serial.println("Scanning...");

  for(byte addr=1; addr<127; addr++){
    Wire.beginTransmission(addr);
    if(Wire.endTransmission()==0){
      Serial.print("Found: 0x");
      Serial.println(addr,HEX);
    }
  }
}

void loop(){}