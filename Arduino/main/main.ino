#include <Servo.h>

// === Pin Configuration ===
#define ADC_VREF 3.3
#define ADC_RESOLUTION 1024.0
#define PIN_TMP36 A0
#define PIN_MOIST A2
#define servoPin 9

Servo myServo;
int servoPosition = 90; // Default servo angle

// === Averaging Buffers ===
const int NUM_SAMPLES = 5;
float tempSamples[NUM_SAMPLES] = {0};
int moistureSamples[NUM_SAMPLES] = {0};
int sampleIndex = 0;
bool filled = false;

void setup()
{
    Serial.begin(9600);
    myServo.attach(servoPin);
    myServo.write(servoPosition);
    analogReference(EXTERNAL); // Use external 3.3V reference on AREF
    delay(1000);               // Let everything settle
}

void loop()
{
    handleSerialInput(); // Respond to PC commands
    sendSensorData();    // Output averaged sensor data
    delay(500);          // Adjust as needed
}

// === Handle incoming serial commands (e.g., servo control) ===
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

// === Read and send sensor data ===
void sendSensorData()
{
    int rawMoisture = analogRead(PIN_MOIST);
    float rawTemp = tmp_conv(analogRead(PIN_TMP36));

    // Store new readings in circular buffers
    moistureSamples[sampleIndex] = rawMoisture;
    tempSamples[sampleIndex] = rawTemp;

    sampleIndex++;
    if (sampleIndex >= NUM_SAMPLES)
    {
        sampleIndex = 0;
        filled = true;
    }

    // Calculate averages
    int avgMoisture = averageMoisture();
    float avgTemp = averageTemp();

    // Serial output
    Serial.print("MOIST:");
    Serial.println(avgMoisture);

    Serial.print("TEMP:");
    Serial.println(avgTemp, 2); // Print with 2 decimal places
}

// === Convert TMP36 analog reading to temperature in °C ===
float tmp_conv(int adcVal)
{
    float voltage = adcVal * (ADC_VREF / ADC_RESOLUTION);
    float tempC = (voltage - 0.5) * 100.0;
    return tempC;
}

// === Compute average temperature ===
float averageTemp()
{
    float sum = 0;
    int count = filled ? NUM_SAMPLES : sampleIndex;
    for (int i = 0; i < count; i++)
    {
        sum += tempSamples[i];
    }
    return (count > 0) ? sum / count : 0;
}

// === Compute average moisture ===
int averageMoisture()
{
    int sum = 0;
    int count = filled ? NUM_SAMPLES : sampleIndex;
    for (int i = 0; i < count; i++)
    {
        sum += moistureSamples[i];
    }
    return (count > 0) ? sum / count : 0;
}
