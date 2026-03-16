// VERSION 1.0

/*  DELTA Robot Control Software
    Copyright (c) 2026, Satyendra
    All rights reserved.
*/

// VERSION LOG
// 1.0 - 3/16/26 - initial release

const char *FIRMWIRE_VERSION = "6.6";

#include <Arduino.h>
#include <math.h>

//========== CONSTANTS ==========
const float STEPS_PER_DEGREE = 4.444444;   // Steps per degree (old code value)
const float pi = 3.141592653;
const float SQRT3 = sqrt(3.0);
const float dtr = pi / 180.0;               // Degrees to radians (old code)

//========== PIN DEFINITIONS ==========
const int PUL[] = {10, 8, 6};               // Pulse pins
const int DIR[] = {11, 9, 7};                // Direction pins
const int ENA[] = {A3, A4, A5};              // Enable pins
const int SENSOR[] = {12, 5, 4};             // Limit sensors
const int ALM[] = {A0, A1, A2};               // Alarm pins (old code)
const int ESTOP_PIN = 2;                      // Emergency stop

//========== ROBOT GEOMETRY (OLD CODE) ==========
const float e = 75.0;        // End effector
const float f = 100.0;       // Base
const float re = 576.0;      // Upper arm
const float rf = 192.0;       // Lower arm

//========== MOTOR VARIABLES ==========
int motDir[] = {1, 1, 1};                    // Motor direction
int calDir[] = {0, 0, 0};                    // Calibration direction
int limPos[] = {90, 90, 90};                  // Positive limits
int limNeg[] = {-90, -90, -90};               // Negative limits
float calOffset[] = {0, 0, 0};                // Calibration offset

//========== DERIVED VALUES ==========
int stepLimPos[3], stepLimNeg[3], zeroStep[3], stepPos[3];
int calStepOffset[3];
int homed[3] = {0, 0, 0};
int error[3] = {0, 0, 0};

//========== POSITION VARIABLES ==========
float currentAngles[] = {0.0, 0.0, 0.0};      // Current angles (old code)
volatile bool systemFault = false;

//========== KINEMATICS FUNCTIONS (OLD CODE EXACT) ==========

int delta_calcAngleYZ(float x0, float y0, float z0, float &theta) {
    float wb = f / (2 * SQRT3); 
    float wp = e / (2 * SQRT3); 
    float y1 = -wb; 
    y0 -= wp; 
    
    float a = (x0 * x0 + y0 * y0 + z0 * z0 + rf * rf - re * re - y1 * y1) / (2 * z0);
    float b = (y1 - y0) / z0;
    float d = -(a + b * y1) * (a + b * y1) + rf * (b * b * rf + rf);
    
    if (d < 0) return -1; 
    float yj = (y1 - a * b - sqrt(d)) / (b * b + 1); 
    float zj = a + b * yj;
    theta = 180.0 * atan(-zj / (y1 - yj)) / pi + ((yj > y1) ? 180.0 : 0.0);
    return 0;
}

int delta_calcInverse(float x0, float y0, float z0, float &t1, float &t2, float &t3) {
    float cos120 = -0.5; 
    float sin120 = 0.866025;
    int status = delta_calcAngleYZ(x0, y0, z0, t1);
    if (status == 0) status = delta_calcAngleYZ(x0*cos120 + y0*sin120, y0*cos120 - x0*sin120, z0, t2);
    if (status == 0) status = delta_calcAngleYZ(x0*cos120 - y0*sin120, y0*cos120 + x0*sin120, z0, t3);
    return status;
}

//========== CALIBRATION (OLD CODE DOUBLE-TOUCH LOGIC) ==========

void calibrateSynced() {
    if(systemFault) return;
    Serial.println(F("Starting Ultra-Slow Double-Touch Calibration..."));

    for(int i=0; i<3; i++) {
        digitalWrite(ENA[i], LOW);
        digitalWrite(DIR[i], LOW); // Move UP
    }
    
    bool triggered[] = {false, false, false};

    // --- STEP 1: First Touch ---
    while (!(triggered[0] && triggered[1] && triggered[2])) {
        if (systemFault) return;
        for (int i = 0; i < 3; i++) {
            if (digitalRead(SENSOR[i]) == HIGH) {
                digitalWrite(PUL[i], HIGH);
            } else {
                triggered[i] = true;
            }
        }
        delayMicroseconds(20000); // 20ms High
        for (int i = 0; i < 3; i++) digitalWrite(PUL[i], LOW);
        delayMicroseconds(20000); // 20ms Low
    }

    Serial.println(F("First touch done. Backing off 15 degrees..."));
    delay(1000); 

    // --- STEP 2: 15 Degree Backoff ---
    for(int i=0; i<3; i++) digitalWrite(DIR[i], HIGH); // Move DOWN
    long backSteps = 15 * STEPS_PER_DEGREE;
    for(long s=0; s < backSteps; s++) {
        for(int i=0; i<3; i++) digitalWrite(PUL[i], HIGH);
        delayMicroseconds(10000);
        for(int i=0; i<3; i++) digitalWrite(PUL[i], LOW);
        delayMicroseconds(10000);
    }

    delay(1000);

    // --- STEP 3: Final Precision Touch ---
    Serial.println(F("Final precision touch starting..."));
    for(int i=0; i<3; i++) {
        digitalWrite(DIR[i], LOW); // Move UP again
        triggered[i] = false;
    }

    while (!(triggered[0] && triggered[1] && triggered[2])) {
        if (systemFault) return;
        for (int i = 0; i < 3; i++) {
            if (digitalRead(SENSOR[i]) == HIGH) {
                digitalWrite(PUL[i], HIGH);
            } else {
                triggered[i] = true; 
            }
        }
        delayMicroseconds(30000); // Super Slow precision
        for (int i = 0; i < 3; i++) digitalWrite(PUL[i], LOW);
        delayMicroseconds(30000);
    }

    Serial.println(F("Precision touch complete. Moving to 90 degree offset..."));
    delay(1000); 

    // --- STEP 4: 90 Degree Offset Move ---
    for(int i=0; i<3; i++) digitalWrite(DIR[i], HIGH); // Move DOWN
    
    long offsetSteps = 90 * STEPS_PER_DEGREE;
    for(long s=0; s < offsetSteps; s++) {
        if (systemFault) return;
        for(int i=0; i<3; i++) {
            digitalWrite(PUL[i], HIGH);
        }
        delayMicroseconds(10000);
        for(int i=0; i<3; i++) {
            digitalWrite(PUL[i], LOW);
        }
        delayMicroseconds(10000);
    }

    for(int i=0; i<3; i++) {
        currentAngles[i] = 0.0;
        homed[i] = 1;
    }
    Serial.println(F("DELTA CALIBRATION SUCCESSFUL. READY AT 0."));
}

//========== MOVEMENT (OLD CODE SYNC MOVE LOGIC) ==========

void syncMove(float targets[], float duration) {
    long totalSteps[3];
    long stepsDone[] = {0, 0, 0};
    
    for(int i=0; i<3; i++) {
        float delta = targets[i] - currentAngles[i];
        totalSteps[i] = round(abs(delta) * STEPS_PER_DEGREE);
        digitalWrite(DIR[i], (delta >= 0) ? HIGH : LOW);
    }
    
    unsigned long startTime = millis();
    unsigned long durationMs = duration * 50;  // Old code multiplier
    
    while (millis() < (startTime + durationMs)) {
        if (systemFault) return;
        float t = (float)(millis() - startTime) / (float)durationMs;
        float smooth = t * t * (3.0 - 2.0 * t); 

        for(int i=0; i<3; i++) {
            long targetStepNow = round(smooth * totalSteps[i]);
            while(stepsDone[i] < targetStepNow) {
                digitalWrite(PUL[i], HIGH); 
                delayMicroseconds(10);
                digitalWrite(PUL[i], LOW); 
                delayMicroseconds(10);
                stepsDone[i]++;
            }
        }
    }
    
    for(int i=0; i<3; i++) {
        currentAngles[i] = targets[i];
        stepPos[i] = targets[i] * STEPS_PER_DEGREE; // Update step position
    }
}



//========== SETUP ==========

void setup() {
    Serial.begin(9600);
    
    // Initialize pins
    for(int i=0; i<3; i++) {
        pinMode(PUL[i], OUTPUT);
        pinMode(DIR[i], OUTPUT);
        pinMode(ENA[i], OUTPUT);
        pinMode(SENSOR[i], INPUT_PULLUP);
        pinMode(ALM[i], INPUT_PULLUP);  // Old code alarm pins
        digitalWrite(ENA[i], LOW);
    }
    
    pinMode(ESTOP_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(ESTOP_PIN), []{ systemFault = true; }, FALLING);
    
    // Calculate derived values
    for(int i=0; i<3; i++) {
        stepLimPos[i] = limPos[i] * STEPS_PER_DEGREE;
        stepLimNeg[i] = abs(limNeg[i]) * STEPS_PER_DEGREE;
        zeroStep[i] = stepLimNeg[i];
        stepPos[i] = zeroStep[i];
        calStepOffset[i] = calOffset[i] * STEPS_PER_DEGREE;
    }
    
    Serial.println(F("DELTA OS INITIALIZED. Send 'JC' for Home."));
}

//========== LOOP ==========

//========== LOOP (SIMPLIFIED FIX) ==========

void loop() {
    if(systemFault) {
        for(int i=0; i<3; i++) digitalWrite(ENA[i], HIGH);
        Serial.println(F("FAULT ACTIVE. Type 'RESET' to clear."));
        delay(1000);
        return;
    }
    
    if(Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        
        // Don't convert to uppercase yet
        String upperCmd = cmd;
        upperCmd.toUpperCase();

        if(upperCmd == "JC") {
            calibrateSynced();
        }
        else if(upperCmd == "RESET") {
            systemFault = false;
            for(int i=0; i<3; i++) digitalWrite(ENA[i], LOW);
            Serial.println(F("SYSTEM_RESET_OK"));
        }
        else if(upperCmd.startsWith("GOTO")) {
            // Parse using the original cmd (with original case)
            float x, y, z, t;
            
            // Simple parsing manually
            int firstSpace = cmd.indexOf(' ');
            int secondSpace = cmd.indexOf(' ', firstSpace + 1);
            int thirdSpace = cmd.indexOf(' ', secondSpace + 1);
            int fourthSpace = cmd.indexOf(' ', thirdSpace + 1);
            
            if(firstSpace > 0 && secondSpace > 0 && thirdSpace > 0) {
                x = cmd.substring(firstSpace + 1, secondSpace).toFloat();
                y = cmd.substring(secondSpace + 1, thirdSpace).toFloat();
                z = cmd.substring(thirdSpace + 1, fourthSpace).toFloat();
                t = cmd.substring(fourthSpace + 1).toFloat();
                
                float t1, t2, t3;
                if(delta_calcInverse(x, y, z, t1, t2, t3) == 0) {
                    float targets[] = {t1, t2, t3};
                    syncMove(targets, t);
                    Serial.println(F("DONE"));
                } else {
                    Serial.println(F("OUT_OF_RANGE"));
                }
            } else {
                Serial.println(F("Usage: GOTO x y z time"));
            }
        }
        else if(cmd.length() > 0) {
            Serial.print(F("Unknown: ")); Serial.println(cmd);
        }
    }
}