#include <Servo.h>

// === Pin Configuration ===
#define ADC_VREF 3.3 // in volt
#define ADC_RESOLUTION 1024.0
#define PIN_TMP36 A0
#define PIN_MOIST A2
#define servoPin 9

Servo myServo;
int servoPosition = 90; // Default servo angle

void setup()
{
    Serial.begin(9600);
    myServo.attach(servoPin);
    myServo.write(servoPosition);
    analogReference(EXTERNAL);
    delay(1000); // Let servo stabilise
}

void loop()
{
    handleSerialInput(); // Check for incoming commands
    sendSensorData();    // Send both MOIST and TEMP data
    delay(500);          // Adjust as needed
}

// === Serial Command Handler ===
void handleSerialInput()
{
    if (Serial.available())
    {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command.startsWith("SET_SERVO:"))
        {
            int pos = command.substring(10).toInt();
            pos = constrain(pos, 0, 180);
            myServo.write(pos);
            servoPosition = pos;
            Serial.print("ACK_SERVO:");
            Serial.println(pos);
        }
    }
}

// === Send Sensor Readings ===
void sendSensorData()
{
    int moisture = analogRead(PIN_MOIST) * (ADC_VREF / 5);
    float temp = tmp_conv(analogRead(PIN_TMP36));

    Serial.print("MOIST:");
    Serial.println(moisture);

    Serial.print("TEMP:");
    Serial.println(temp);
}

float tmp_conv(int adcVal){
    // convert the ADC value to voltage
    float voltage = adcVal * (ADC_VREF / ADC_RESOLUTION);
    // convert the voltage to the temperature in Celsius
    float tempC = (voltage - 0.5) * 100;
    // convert the Celsius to Fahrenheit
    float tempF = tempC * 9 / 5 + 32;

    return tempC;
}