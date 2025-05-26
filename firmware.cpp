#include <Servo.h>
//Pin Assignment as our schematic digram
#define ADC_VREF 5.0
#define ADC_RESOLUTION 1024.0
#define PIN_TMP36 A2
#define PIN_SOIL A5
#define SERVO_PIN 9

const int NUM_SAMPLES = 10;

Servo myservo;

void setup() {
  Serial.begin(9600);
  myservo.attach(SERVO_PIN);
}

float readAveragedAnalog(int pin) {
  long sum = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    sum += analogRead(pin);
    delay(5);  // small delay to allow ADC to settle
  }
  return sum / float(NUM_SAMPLES);
}

void loop() {
  // Average Sampling TMP36 and Soil moisture sensor
  float adcTemp = readAveragedAnalog(PIN_TMP36);
  float adcSoil = readAveragedAnalog(PIN_SOIL);

  // Conversion from TMP36 voltage ouput to temperature
  float voltage = adcTemp * (ADC_VREF / ADC_RESOLUTION);
  float tempC = (voltage - 0.5) * 100;

  // send temperature and moisture to pc end
  Serial.print("T=");
  Serial.print(tempC, 1);  // 保留一位小数
  Serial.print(",M=");
  Serial.println((int)adcSoil);  // 湿度保留整数即可

  // recieve excuting signal form computer
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("SERVO=")) {
      int angle = cmd.substring(6).toInt();
      myservo.write(angle);
    }
  }

  delay(1000);  // every second
}
