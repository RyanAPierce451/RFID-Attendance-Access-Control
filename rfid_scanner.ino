#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

#define Servo_PWM 6
#define SS_PIN 10
#define RST_PIN 9
#define ACCESS_POINT_ID "R231"

Servo MG995_Servo;
MFRC522 rfid(SS_PIN, RST_PIN);

bool isGateOpen = false;
unsigned long startTimer = 0;
const unsigned long delayTime = 30000;
bool timerActive = false;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  MG995_Servo.attach(Servo_PWM);
  MG995_Servo.write(0); // Assume gate is closed initially
}

void loop() {
  // Check for new RFID card
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    // Print the UID of the card
    Serial.print(ACCESS_POINT_ID);
    Serial.print(" ");
    printUid(rfid.uid.uidByte, rfid.uid.size);
    Serial.println();

    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();

    // Wait for response from an external system
    if (Serial.available()) {
      char response = Serial.read();
      handleResponse(response);
    }
  }

  // Timer actions independent of RFID scanning
  if (timerActive && millis() - startTimer >= delayTime) {
    MG995_Servo.write(0); // Move servo to close position
    isGateOpen = false;
    timerActive = false;
  }
}

void handleResponse(char response) {
  if (response == '1' && !isGateOpen) {
    MG995_Servo.write(180); // Move servo to open position
    isGateOpen = true;
    startTimer = millis();
    timerActive = true;
  } else if (response == '0' && isGateOpen) {
    MG995_Servo.write(0); // Move servo to close position
    isGateOpen = false;
  }
}

void printUid(byte *buffer, byte bufferSize) {
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
  }
}
