#include "ArduinoGraphics.h"
#include "Arduino_LED_Matrix.h"

ArduinoLEDMatrix matrix;

const int RELAY_PIN = A5;
const int LED_PIN = 13; 

void setup() {
  Serial.begin(115200); 
  matrix.begin();
  
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  matrix.clear(); 
  matrix.stroke(0xFFFFFF);
  matrix.textScrollSpeed(90);
  matrix.textFont(Font_5x7);
  matrix.beginText(4, 1, 0xFFFFFF); 
  matrix.println("READY");
  matrix.endText(SCROLL_LEFT);
  delay(2000); 
  closeDoor();
}

void loop() {
  if (Serial.available()) { // Check if there's data coming from Python
    String command = Serial.readString(); // Read the incoming command
    
    if (command == "openDoor") {
      openDoor();
    }
    else if (command == "closeDoor") {
      closeDoor();
    }
  }
}

void closeDoor() {
  // LOCK DOOR
  digitalWrite(RELAY_PIN, LOW); 
  digitalWrite(LED_PIN, HIGH);
  
  matrix.clear(); 
  matrix.stroke(0xFFFFFF); 
  matrix.textFont(Font_5x7);
  matrix.beginText(4, 1, 0xFFFFFF); 
  matrix.println("C"); 
  matrix.endText();

  Serial.println("Door Closed");
}

void openDoor() {
  // UNLOCK DOOR
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(LED_PIN, LOW);

  matrix.clear(); 
  matrix.stroke(0xFFFFFF);
  matrix.textScrollSpeed(90);
  matrix.beginText(4, 1, 0xFFFFFF);
  matrix.println("O"); 
  matrix.endText();

  Serial.println("Door Opened");
}
