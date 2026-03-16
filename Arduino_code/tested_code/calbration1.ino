#include <Arduino.h>
#include <math.h>

// ==========================================
// 1. Robot Geometry (400mm Radius Finalized)
// ==========================================
const float e = 75.0;     
const float f = 100.0;     
const float re = 576.0;    
const float rf = 192.0;    

const float sqrt3 = sqrt(3.0);
const float pi = 3.141592653;
const float dtr = pi / 180.0;

// ==========================================
// 2. Hardware Configuration
// ==========================================
const int PUL[] = {10, 8, 6}; 
const int DIR[] = {11, 9, 7};
const int ALM[] = {A0, A1, A2};
const int SENSOR[] = {12, 5, 4};
const int ENA[] = {A3, A4, A5}; 
const int ESTOP_PIN = 2;

const float STEPS_PER_DEGREE = 4.444444; 
float currentAngles[] = {0.0, 0.0, 0.0}; 
volatile bool systemFault = false;

// ==========================================
// 3. Kinematics Engine
// ==========================================

int delta_calcAngleYZ(float x0, float y0, float z0, float &theta) {
    float wb = f / (2 * sqrt3); 
    float wp = e / (2 * sqrt3); 
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
    float cos120 = -0.5; float sin120 = 0.866025;
    int status = delta_calcAngleYZ(x0, y0, z0, t1);
    if (status == 0) status = delta_calcAngleYZ(x0*cos120 + y0*sin120, y0*cos120 - x0*sin120, z0, t2);
    if (status == 0) status = delta_calcAngleYZ(x0*cos120 - y0*sin120, y0*cos120 + x0*sin120, z0, t3);
    return status;
}

// ==========================================
// 4. Double-Touch Smart Calibration (Final Fixed)
// ==========================================

void calibrateSynced() {
    if(systemFault) return;
    Serial.println(F("Starting Ultra-Slow Double-Touch Calibration..."));

    for(int i=0; i<3; i++) {
        digitalWrite(ENA[i], LOW);
        digitalWrite(DIR[i], LOW); // Move UP
    }
    
    bool homed[] = {false, false, false};

    // --- STEP 1: First Touch ---
    while (!(homed[0] && homed[1] && homed[2])) {
        if (systemFault) return;
        for (int i = 0; i < 3; i++) {
            if (digitalRead(SENSOR[i]) == HIGH) {
                digitalWrite(PUL[i], HIGH);
            } else {
                homed[i] = true;
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
        homed[i] = false; // Reset status for second touch
    }

    while (!(homed[0] && homed[1] && homed[2])) {
        if (systemFault) return;
        for (int i = 0; i < 3; i++) {
            if (digitalRead(SENSOR[i]) == HIGH) {
                digitalWrite(PUL[i], HIGH);
            } else {
                homed[i] = true; 
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

    for(int i=0; i<3; i++) currentAngles[i] = 0.0;
    Serial.println(F("DELTA CALIBRATION SUCCESSFUL. READY AT 0."));
}

// ==========================================
// 5. Coordinated Movement Engine
// ==========================================

void syncMove(float targets[], float duration) {
    long totalSteps[3];
    long stepsDone[] = {0, 0, 0};
    for(int i=0; i<3; i++) {
        float delta = targets[i] - currentAngles[i];
        totalSteps[i] = round(abs(delta) * STEPS_PER_DEGREE);
        digitalWrite(DIR[i], (delta >= 0) ? HIGH : LOW);
    }
    unsigned long startTime = millis();
    unsigned long durationMs = duration * 50;
    
    while (millis() < (startTime + durationMs)) {
        if (systemFault) return;
        float t = (float)(millis() - startTime) / (float)durationMs;
        float smooth = t * t * (3.0 - 2.0 * t); 

        for(int i=0; i<3; i++) {
            long targetStepNow = round(smooth * totalSteps[i]);
            while(stepsDone[i] < targetStepNow) {
                digitalWrite(PUL[i], HIGH); delayMicroseconds(10);
                digitalWrite(PUL[i], LOW); delayMicroseconds(10);
                stepsDone[i]++;
            }
        }
    }
    for(int i=0; i<3; i++) currentAngles[i] = targets[i];
}

// ==========================================
// 6. Setup & Main Loop
// ==========================================

void setup() {
    Serial.begin(9600);
    for(int i=0; i<3; i++) {
        pinMode(PUL[i], OUTPUT); pinMode(DIR[i], OUTPUT);
        pinMode(ENA[i], OUTPUT); pinMode(SENSOR[i], INPUT_PULLUP);
        pinMode(ALM[i], INPUT_PULLUP);
        digitalWrite(ENA[i], LOW); 
    }
    pinMode(ESTOP_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(ESTOP_PIN), []{ systemFault = true; }, FALLING);
    
    Serial.println(F("DELTA OS INITIALIZED. Send 'JC' for Home."));
}

void loop() {
    if (systemFault) {
        for(int i=0; i<3; i++) digitalWrite(ENA[i], HIGH);
        Serial.println(F("FAULT ACTIVE. Type 'RESET' to clear."));
        delay(1000);
        return;
    }

    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim(); input.toUpperCase();

        if (input == "JC") {
            calibrateSynced();
        } 
        else if (input == "RESET") {
            systemFault = false;
            for(int i=0; i<3; i++) digitalWrite(ENA[i], LOW);
            Serial.println(F("SYSTEM_RESET_OK"));
        }
        else if (input.startsWith("GOTO")) {
            char str[64]; input.substring(5).toCharArray(str, 64);
            float x = atof(strtok(str, " "));
            float y = atof(strtok(NULL, " "));
            float z = atof(strtok(NULL, " "));
            float mt = atof(strtok(NULL, " "));
            float t1, t2, t3;
            if (delta_calcInverse(x, y, z, t1, t2, t3) == 0) {
                float targets[] = {t1, t2, t3};
                syncMove(targets, mt);
                Serial.println(F("DONE"));
            } else Serial.println(F("OUT_OF_RANGE"));
        }
    }
}