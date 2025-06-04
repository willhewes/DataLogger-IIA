#include <Servo.h>

// === Pin Configuration ===
#define ADC_VREF 3.3
#define ADC_RESOLUTION 1024.0
#define PIN_TMP36 A0
#define PIN_MOIST A2
#define servoPin 9
#define closed_pos 0 // Work out needed positions
#define open_pos 10
#define watering_time 1000 // ms

Servo myServo;

void setup()
{
    Serial.begin(9600);
    myServo.attach(servoPin);
    myServo.write(closed_pos);
    analogReference(EXTERNAL); // Use external 3.3V reference on AREF
    delay(1000);               // Let everything settle
}

void loop()
{
    handleSerialInput(); // Respond to PC commands
    sendSensorData();    // Output averaged sensor data
    delay(50);          // Adjust as needed
}

// Handle incoming serial commands 
void handleSerialInput()
{
    if (Serial.available())
    {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command == "STEP_SERVO")
        {
            myServo.write(open_pos);
            Serial.println("Open");
            delay(watering_time);
            myServo.write(closed_pos);
            Serial.println("Closed");
        }
    }
}

// === Read and send sensor data ===
void sendSensorData()
{
    int rawMoisture = analogRead(PIN_MOIST) * (ADC_VREF / 5);
    float rawTemp = tmp_conv(analogRead(PIN_TMP36));

    // Serial output
    Serial.print(rawMoisture);

    Serial.print(",");
    Serial.println(rawTemp, 2); // Print with 2 decimal places
}

// === Convert TMP36 analog reading to temperature in °C ===
float tmp_conv(int adcVal)
{
    float voltage = adcVal * (ADC_VREF / ADC_RESOLUTION);
    float tempC = (voltage - 0.5) * 100.0;
    return tempC;
}