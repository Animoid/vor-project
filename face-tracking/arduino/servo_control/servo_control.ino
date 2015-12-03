#include <Servo.h> 


const int ledPin = 13;
String s = "";

Servo pan_servo;  
Servo tilt_servo;


float toFloat(String str)
{
  char buffer[32];
  str.toCharArray(buffer, 32);
  return atof(buffer);
}

void blink(int numberOfTimes){
  for (int i = 0; i < numberOfTimes; i++)  {
    digitalWrite(ledPin, HIGH);
    delay(200);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
}

void setup(){
  pinMode(ledPin, OUTPUT);
  pan_servo.attach(9);  
  tilt_servo.attach(10);
  Serial.begin(38400);
  //blink(2);
  
  // move servos to pratical pan/tilt head limits
  tilt_servo.write(105);
  pan_servo.write(30.0);
  delay(500);
  pan_servo.write(150.0);
  delay(500);
  pan_servo.write(87.0);
  delay(500);
  
  tilt_servo.write(60);
  delay(500);
  tilt_servo.write(160);
  delay(500);
  tilt_servo.write(106);
  
  
}

const int StartByte = 1; // SOH
const int PacketEnd = 4; // EOT
const int PacketACK = 6; // ACK
const int PacketNAK = 21; // NAK


const int BlinkCmd = 10;
const int PanTiltCmd = 11;


int interpretSerialPacket()
{
  int start = Serial.read();
  if (start != StartByte) {
    s = Serial.readStringUntil(PacketEnd);
    Serial.write(PacketNAK);
    Serial.write('s');
    Serial.flush();
    return -1; // bad packet or started in mid-packet
  }
  if (!Serial.available()) {  // wait for next byte
    int t = 0;
    while (!Serial.available() && t < 50) {
      delay(1);
      t += 1;
    }
    if (t >= 50) {
      Serial.write(PacketNAK);
      Serial.write('t');
      Serial.flush();
      return -4;
    }
  }
  int version = Serial.read();
  int cmd = 0;
  if (version == 65) { // 'A'
    cmd = Serial.readStringUntil('\n').toInt();
    if (cmd == BlinkCmd) {
      int blinkCount = Serial.readStringUntil('\n').toInt();
      blink(blinkCount);
    }
    else if (cmd == PanTiltCmd) {
      float panAngle = toFloat(Serial.readStringUntil('\n'));
      float tiltAngle = toFloat(Serial.readStringUntil('\n'));
      pan_servo.write(panAngle);
      tilt_servo.write(tiltAngle);
    }
    else {
      Serial.readStringUntil(PacketEnd);
      Serial.write(PacketNAK);
      Serial.write('?');
      Serial.flush();
      return -3; // unsupported command
    }
  }
  else {
    Serial.readStringUntil(PacketEnd);
    Serial.write(PacketNAK);
    Serial.write('v');
    Serial.flush();
    return -2; // unsupported protocol version
  }
  Serial.readStringUntil(PacketEnd);
  Serial.write(PacketACK);
  Serial.write(cmd);
  Serial.flush();
  return 1;
}



void loop(){
  if (Serial.available())  {
     interpretSerialPacket();
  }
  delay(2);
}

