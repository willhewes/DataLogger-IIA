#include <Servo.h>

Servo myservo; // create servo object to control a servo
int pos = 0;   // variable to store the servo position

void setup()
{
    myservo.attach(9); // attaches the servo on pin 9 to the servo object

    // Sweep from 0 to 180 degrees
    for (pos = 0; pos <= 180; pos++)
    {
        myservo.write(pos);
        delay(15);
    }

    // Sweep back to 0 degrees
    for (pos = 180; pos >= 0; pos--)
    {
        myservo.write(pos);
        delay(15);
    }
}

void loop()
{
    // Do nothing after one sweep
}
