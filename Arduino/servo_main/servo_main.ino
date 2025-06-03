#include <Servo.h>

Servo myservo; // create servo object to control a servo
int pos = 0;   // variable to store the servo position
int pos_closed = 15; // variable to do closed position
bool open = false;

void setup()
{
    myservo.attach(9); // attaches the servo on pin 9 to the servo object
}

void loop()
{
    if (open)
    {
        for (pos = 0; pos <= pos_closed; pos++)
        {
            myservo.write(pos);
            delay(15);
        }
    }
    
    if (!open)
    {
        // Sweep back to 0 degrees
        for (pos = pos_closed; pos >= 0; pos--)
        {
            myservo.write(pos);
            delay(15);
        }
    }
}
