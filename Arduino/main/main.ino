#include <Servo.h>

// === Pin Configuration ===
#define ADC_VREF 3.3
#define ADC_RESOLUTION 1024.0
#define PIN_TMP36 A0
#define PIN_MOIST A2
#define servoPin 9
#define closed_pos 0 // Work out needed positions
#define open_pos 40
#define watering_time 1000 // ms

unsigned long lastWateringTime = 0;
unsigned long wateringCooldown = 10000; // 10 seconds cooldown in milliseconds

// Threshold levels
int moist_thresh_min = -1;

// Warning thresholds
float temp_warn_min = -999;
float temp_warn_max = 999;
int moist_warn_min = -1;
int moist_warn_max = 1024;

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

    int rawMoisture = analogRead(PIN_MOIST);
    int Moisture = convertMoistureToPercent(rawMoisture);

    float rawTemp = tmp_conv(analogRead(PIN_TMP36));

    checkThresholdAndWater(Moisture, rawTemp);
    sendSensorData(Moisture, rawTemp);

    delay(50);
}

void checkThresholdAndWater(int moisture, float temp)
{
    unsigned long now = millis();
    if (moisture < moist_thresh_min)
    {
        water();
    }
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
            water();
        }
        else if (command.startsWith("SET_THRESH "))
        {
            parseThresholdCommand(command);
        }
        else if (command.startsWith("SET_WARN "))
        {
            parseWarningCommand(command);
        }
    }
}

// === Read and send sensor data ===
void sendSensorData(int Moisture, float rawTemp)
{
    Serial.print(Moisture);
    Serial.print(",");
    Serial.println(rawTemp, 2);
}

// === Convert TMP36 analog reading to temperature in °C ===
float tmp_conv(int adcVal)
{
    float voltage = adcVal * (ADC_VREF / ADC_RESOLUTION);
    float tempC = (voltage - 0.5) * 100.0;
    return tempC;
}

int convertMoistureToPercent(int rawVal)
{
    const int dry = 520;
    const int wet = 250;

    // Clamp value within bounds
    if (rawVal > dry)
        rawVal = dry;
    if (rawVal < wet)
        rawVal = wet;

    // Linear mapping
    int percent = (dry - rawVal) * 100 / (dry - wet);
    return percent;
}

void parseThresholdCommand(const String &command)
{
    if (!command.startsWith("SET_THRESH "))
        return;

    String rest = command.substring(11); // Remove "SET_THRESH "
    int firstSpace = rest.indexOf(' ');
    int secondSpace = rest.indexOf(' ', firstSpace + 1);

    if (firstSpace == -1 || secondSpace == -1)
        return;

    String sensor = rest.substring(0, firstSpace);
    float minVal = rest.substring(firstSpace + 1, secondSpace).toFloat();

    if (sensor == "moisture")
    {
        minVal = constrain(minVal, 0, 100);
        moist_thresh_min = (int)minVal;
        Serial.println("Moisture threshold limits updated");
    }
}

void parseWarningCommand(const String &command)
{
    if (!command.startsWith("SET_WARN "))
        return;

    String rest = command.substring(9); // Remove "SET_WARN "
    int firstSpace = rest.indexOf(' ');
    int secondSpace = rest.indexOf(' ', firstSpace + 1);

    if (firstSpace == -1 || secondSpace == -1)
        return;

    String sensor = rest.substring(0, firstSpace);
    float minVal = rest.substring(firstSpace + 1, secondSpace).toFloat();
    float maxVal = rest.substring(secondSpace + 1).toFloat();

    if (sensor == "temp_C")
    {
        temp_warn_min = minVal;
        temp_warn_max = maxVal;
        Serial.println("Temp warning limits updated");
    }
    else if (sensor == "moisture")
    {
        minVal = constrain(minVal, 0, 100);
        maxVal = constrain(maxVal, 0, 100);
        moist_warn_min = (int)minVal;
        moist_warn_max = (int)maxVal;
        Serial.println("Moisture warning limits updated");
    }
}

void water()
{
    unsigned long now = millis();
    if (now - lastWateringTime < wateringCooldown)
        return; // Too soon, skip watering

    lastWateringTime = now;

    myServo.write(open_pos);
    Serial.println("Open");
    delay(watering_time);
    myServo.write(closed_pos);
    Serial.println("Closed");
}
