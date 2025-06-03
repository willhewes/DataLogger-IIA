/*
 * Created by ArduinoGetStarted.com
 *
 * This example code is in the public domain
 *
 * Tutorial page: https://arduinogetstarted.com/tutorials/arduino-tmp36-temperature-sensor
 */

#define ADC_VREF 3.3 // in volt
#define ADC_RESOLUTION 1024.0
#define PIN_TMP36 A0

void setup()
{
    Serial.begin(9600);
    analogReference(EXTERNAL); // set the voltage reference from VREF pin
}

void loop()
{
    // get the ADC value from the TMP36 temperature sensor
    int adcVal = analogRead(PIN_TMP36);
    // convert the ADC value to voltage
    float voltage = adcVal * (ADC_VREF / ADC_RESOLUTION);
    // convert the voltage to the temperature in Celsius
    float tempC = (voltage - 0.5) * 100;
    // convert the Celsius to Fahrenheit
    float tempF = tempC * 9 / 5 + 32;

    // print the temperature in the Serial Monitor:
    Serial.print("T:");
    Serial.println(tempC);


    delay(1000);
}
