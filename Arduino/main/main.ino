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

// Threshold levels
float temp_thresh_min = -999;
float temp_thresh_max = 999;
int moist_thresh_min = -1;
int moist_thresh_max = 1024;

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
    float maxVal = rest.substring(secondSpace + 1).toFloat();

    if (sensor == "temp_C")
    {
        temp_thresh_min = minVal;
        temp_thresh_max = maxVal;
        Serial.println("Temp threshold limits updated");
    }
    else if (sensor == "moisture")
    {
        moist_thresh_min = (int)minVal;
        moist_thresh_max = (int)maxVal;
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
        moist_warn_min = (int)minVal;
        moist_warn_max = (int)maxVal;
        Serial.println("Moisture warning limits updated");
    }
}