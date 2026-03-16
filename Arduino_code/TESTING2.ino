// VERSION 1.0 - DELTA ROBOT COMPLETE FIRMWARE

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
const float STEPS_PER_DEGREE = 4.444444;  // Steps per degree
const float pi = 3.141592653;
const float SQRT3 = sqrt(3.0);
const float DTR = pi / 180.0;  // Degrees to radians

//========== PIN DEFINITIONS ==========
const int PUL[] = { 10, 8, 6 };     // Pulse pins
const int DIR[] = { 11, 9, 7 };     // Direction pins
const int ENA[] = { A3, A4, A5 };   // Enable pins
const int SENSOR[] = { 12, 5, 4 };  // Limit sensors
const int ALM[] = { A0, A1, A2 };   // Alarm pins
const int ESTOP_PIN = 2;            // Emergency stop

//========== ROBOT GEOMETRY ==========
const float e = 75.0;    // End effector
const float f = 100.0;   // Base
const float re = 576.0;  // Upper arm
const float rf = 192.0;  // Lower arm

//========== MOTOR VARIABLES ==========
int motDir[] = { 1, 1, 1 };        // Motor direction
int calDir[] = { 0, 0, 0 };        // Calibration direction
int limPos[] = { 90, 90, 90 };     // Positive limits
int limNeg[] = { -90, -90, -90 };  // Negative limits
float calOffset[] = { 0, 0, 0 };   // Calibration offset

//========== DERIVED VALUES ==========
int stepLimPos[3], stepLimNeg[3], zeroStep[3], stepPos[3];
int calStepOffset[3];
int homed[3] = { 0, 0, 0 };
int error[3] = { 0, 0, 0 };

//========== POSITION VARIABLES ==========
float currentX = 0, currentY = 0, currentZ = -200;  // Current Cartesian position
float currentAngles[] = { 0.0, 0.0, 0.0 };          // Current joint angles
volatile bool systemFault = false;
bool rndTrue = false;
float rndSpeed = 0;
String rndData = "";

//========== FORWARD DECLARATIONS ==========
void updatePos();
void sendRobotPos();
void driveMotorsL(int J1step, int J2step, int J3step, int J1dir, int J2dir, int J3dir, float curDelay);
void syncMove(float targets[], float duration);
void moveJ(String inData, bool response, bool precalc, bool simspeed);

//========== KINEMATICS FUNCTIONS ==========
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
  if (status == 0) status = delta_calcAngleYZ(x0 * cos120 + y0 * sin120, y0 * cos120 - x0 * sin120, z0, t2);
  if (status == 0) status = delta_calcAngleYZ(x0 * cos120 - y0 * sin120, y0 * cos120 + x0 * sin120, z0, t3);
  return status;
}

//========== POSITION UPDATE FUNCTIONS ==========
void updatePos() {
  // Update current angles from step positions
  for (int i = 0; i < 3; i++) {
    currentAngles[i] = (float)(stepPos[i] - zeroStep[i]) / STEPS_PER_DEGREE;
  }
  // Note: Forward kinematics would go here to calculate XYZ from angles
  // For now, we keep currentX, currentY, currentZ as last target
}

void sendRobotPos() {
  // Send current Cartesian position
  Serial.print("X");
  Serial.print(currentX);
  Serial.print(" Y");
  Serial.print(currentY);
  Serial.print(" Z");
  Serial.print(currentZ);
  Serial.print(" J1");
  Serial.print(currentAngles[0]);
  Serial.print(" J2");
  Serial.print(currentAngles[1]);
  Serial.print(" J3");
  Serial.println(currentAngles[2]);
}

//========== MOTOR DRIVE FUNCTIONS ==========
void driveMotorsL(int J1step, int J2step, int J3step,
                  int J1dir, int J2dir, int J3dir,
                  float curDelay) {

  int steps[3] = { J1step, J2step, J3step };
  int dirs[3] = { J1dir, J2dir, J3dir };

  // Find max steps
  int maxSteps = 0;
  for (int i = 0; i < 3; i++) {
    if (steps[i] > maxSteps) maxSteps = steps[i];
  }

  if (maxSteps == 0) return;

  // Set directions with motor correction
  for (int i = 0; i < 3; i++) {
    int effectiveDir = dirs[i];
    if (motDir[i] == -1) effectiveDir = !effectiveDir;
    digitalWrite(DIR[i], (effectiveDir == 1) ? HIGH : LOW);
  }

  delayMicroseconds(15);

  // Ensure minimum delay
  float finalDelay = curDelay;
  const float MIN_STEP_DELAY = 20.0;
  if (finalDelay < MIN_STEP_DELAY) finalDelay = MIN_STEP_DELAY;

  // Execute move
  int curSteps[3] = { 0, 0, 0 };

  for (int s = 0; s < maxSteps && !systemFault; s++) {

    float disDelayCur = 0;

    // Step distribution using linear interpolation
    for (int i = 0; i < 3; i++) {
      if (curSteps[i] < steps[i]) {
        unsigned long targetStep = (unsigned long)s * steps[i] / maxSteps;
        if (targetStep > curSteps[i]) {
          digitalWrite(PUL[i], HIGH);
          delayMicroseconds(2);
          digitalWrite(PUL[i], LOW);
          curSteps[i]++;

          // Update position
          if (dirs[i] == 0) {
            stepPos[i]--;
          } else {
            stepPos[i]++;
          }

          delayMicroseconds(30);
          disDelayCur += 30;
        }
      }
    }

    // Main step delay
    unsigned long delay_us = (unsigned long)(finalDelay - disDelayCur);
    if (delay_us < MIN_STEP_DELAY) delay_us = MIN_STEP_DELAY;
    delayMicroseconds(delay_us);
  }

  // Update angles
  for (int i = 0; i < 3; i++) {
    currentAngles[i] = (float)(stepPos[i] - zeroStep[i]) / STEPS_PER_DEGREE;
  }
}

void syncMove(float targets[], float duration) {
  long totalSteps[3];
  long stepsDone[] = { 0, 0, 0 };

  for (int i = 0; i < 3; i++) {
    float delta = targets[i] - currentAngles[i];
    totalSteps[i] = round(abs(delta) * STEPS_PER_DEGREE);
    digitalWrite(DIR[i], (delta >= 0) ? HIGH : LOW);
  }

  unsigned long startTime = millis();
  unsigned long durationMs = duration * 50;

  while (millis() < (startTime + durationMs) && !systemFault) {
    float t = (float)(millis() - startTime) / (float)durationMs;
    float smooth = t * t * (3.0 - 2.0 * t);

    for (int i = 0; i < 3; i++) {
      long targetStepNow = round(smooth * totalSteps[i]);
      while (stepsDone[i] < targetStepNow) {
        digitalWrite(PUL[i], HIGH);
        delayMicroseconds(10);
        digitalWrite(PUL[i], LOW);
        delayMicroseconds(10);
        stepsDone[i]++;

        if (targets[i] >= currentAngles[i]) {
          stepPos[i]++;
        } else {
          stepPos[i]--;
        }
      }
    }
  }

  for (int i = 0; i < 3; i++) {
    currentAngles[i] = targets[i];
  }
}

//========== CALIBRATION FUNCTIONS ==========
void calibrateSynced() {
  if (systemFault) return;
  Serial.println(F("Starting Ultra-Slow Double-Touch Calibration..."));

  for (int i = 0; i < 3; i++) {
    digitalWrite(ENA[i], LOW);
    digitalWrite(DIR[i], LOW);  // Move UP
  }

  bool triggered[] = { false, false, false };

  // STEP 1: First Touch
  while (!(triggered[0] && triggered[1] && triggered[2])) {
    if (systemFault) return;
    for (int i = 0; i < 3; i++) {
      if (digitalRead(SENSOR[i]) == HIGH) {
        digitalWrite(PUL[i], HIGH);
      } else {
        triggered[i] = true;
      }
    }
    delayMicroseconds(20000);
    for (int i = 0; i < 3; i++) digitalWrite(PUL[i], LOW);
    delayMicroseconds(20000);
  }

  Serial.println(F("First touch done. Backing off 15 degrees..."));
  delay(1000);

  // STEP 2: 15 Degree Backoff
  for (int i = 0; i < 3; i++) digitalWrite(DIR[i], HIGH);  // Move DOWN
  long backSteps = 15 * STEPS_PER_DEGREE;
  for (long s = 0; s < backSteps; s++) {
    for (int i = 0; i < 3; i++) digitalWrite(PUL[i], HIGH);
    delayMicroseconds(10000);
    for (int i = 0; i < 3; i++) digitalWrite(PUL[i], LOW);
    delayMicroseconds(10000);
  }

  delay(1000);

  // STEP 3: Final Precision Touch
  Serial.println(F("Final precision touch starting..."));
  for (int i = 0; i < 3; i++) {
    digitalWrite(DIR[i], LOW);  // Move UP again
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
    delayMicroseconds(30000);
    for (int i = 0; i < 3; i++) digitalWrite(PUL[i], LOW);
    delayMicroseconds(30000);
  }

  Serial.println(F("Precision touch complete. Moving to 90 degree offset..."));
  delay(1000);

  // STEP 4: 90 Degree Offset Move
  for (int i = 0; i < 3; i++) digitalWrite(DIR[i], HIGH);  // Move DOWN

  long offsetSteps = 90 * STEPS_PER_DEGREE;
  for (long s = 0; s < offsetSteps; s++) {
    if (systemFault) return;
    for (int i = 0; i < 3; i++) {
      digitalWrite(PUL[i], HIGH);
    }
    delayMicroseconds(10000);
    for (int i = 0; i < 3; i++) {
      digitalWrite(PUL[i], LOW);
    }
    delayMicroseconds(10000);
  }

  for (int i = 0; i < 3; i++) {
    currentAngles[i] = 0.0;
    homed[i] = 1;
    stepPos[i] = zeroStep[i];
  }
  currentX = 0;
  currentY = 0;
  currentZ = -200;
  Serial.println(F("DELTA CALIBRATION SUCCESSFUL. READY AT 0."));
}

//========== MOVE COMMAND FUNCTIONS ==========
void moveJ(String inData, bool response, bool precalc, bool simspeed) {

  int J1dir, J2dir, J3dir;
  int J1axisFault = 0, J2axisFault = 0, J3axisFault = 0;
  int TotalAxisFault = 0;

  // Parse command
  int xStart = inData.indexOf("X");
  int yStart = inData.indexOf("Y");
  int zStart = inData.indexOf("Z");
  int SPstart = inData.indexOf("S");
  int AcStart = inData.indexOf("Ac");
  int DcStart = inData.indexOf("Dc");
  int RmStart = inData.indexOf("Rm");

  float targetX = inData.substring(xStart + 1, yStart).toFloat();
  float targetY = inData.substring(yStart + 1, zStart).toFloat();
  float targetZ = inData.substring(zStart + 1, SPstart).toFloat();

  String SpeedType = inData.substring(SPstart + 1, SPstart + 2);
  float SpeedVal = inData.substring(SPstart + 2, AcStart).toFloat();
  float ACCspd = inData.substring(AcStart + 2, DcStart).toFloat();
  float DCCspd = inData.substring(DcStart + 2, RmStart).toFloat();
  float ACCramp = inData.substring(RmStart + 2).toFloat();

  // Calculate inverse kinematics
  float J1angle, J2angle, J3angle;
  int kinStatus = delta_calcInverse(targetX, targetY, targetZ, J1angle, J2angle, J3angle);

  if (kinStatus != 0) {
    Serial.println(F("ER"));
    return;
  }

  // Calculate destination motor steps
  int J1futStepM = (J1angle + abs(limNeg[0])) * STEPS_PER_DEGREE;
  int J2futStepM = (J2angle + abs(limNeg[1])) * STEPS_PER_DEGREE;
  int J3futStepM = (J3angle + abs(limNeg[2])) * STEPS_PER_DEGREE;

  if (precalc) {
    stepPos[0] = J1futStepM;
    stepPos[1] = J2futStepM;
    stepPos[2] = J3futStepM;
    currentAngles[0] = J1angle;
    currentAngles[1] = J2angle;
    currentAngles[2] = J3angle;
    currentX = targetX;
    currentY = targetY;
    currentZ = targetZ;
    if (response) sendRobotPos();
    return;
  }

  // Calculate delta
  int J1stepDif = stepPos[0] - J1futStepM;
  int J2stepDif = stepPos[1] - J2futStepM;
  int J3stepDif = stepPos[2] - J3futStepM;

  J1dir = (J1stepDif <= 0) ? 1 : 0;
  J2dir = (J2stepDif <= 0) ? 1 : 0;
  J3dir = (J3stepDif <= 0) ? 1 : 0;

  // Check limits
  if (J1dir == 1 && (J1futStepM > stepLimPos[0])) J1axisFault = 1;
  if (J1dir == 0 && (J1futStepM < 0)) J1axisFault = 1;
  if (J2dir == 1 && (J2futStepM > stepLimPos[1])) J2axisFault = 1;
  if (J2dir == 0 && (J2futStepM < 0)) J2axisFault = 1;
  if (J3dir == 1 && (J3futStepM > stepLimPos[2])) J3axisFault = 1;
  if (J3dir == 0 && (J3futStepM < 0)) J3axisFault = 1;

  TotalAxisFault = J1axisFault + J2axisFault + J3axisFault;

  if (TotalAxisFault == 0) {
    if (simspeed) {
      // Use syncMove for simulated speed
      float targets[] = { J1angle, J2angle, J3angle };
      syncMove(targets, SpeedVal);
    } else {
      // Use driveMotorsL
      float stepDelay = 500;  // Default
      if (SpeedType == "s") {
        int maxSteps = max(abs(J1stepDif), max(abs(J2stepDif), abs(J3stepDif)));
        stepDelay = (SpeedVal * 1000000) / maxSteps;
      }
      driveMotorsL(abs(J1stepDif), abs(J2stepDif), abs(J3stepDif),
                   J1dir, J2dir, J3dir, stepDelay);
    }

    currentX = targetX;
    currentY = targetY;
    currentZ = targetZ;
    currentAngles[0] = J1angle;
    currentAngles[1] = J2angle;
    currentAngles[2] = J3angle;

    if (response) sendRobotPos();
  } else {
    String alarm = "EL" + String(J1axisFault) + String(J2axisFault) + String(J3axisFault);
    Serial.println(alarm);
  }
}

void moveLinear(String inData) {

  int J1dir, J2dir, J3dir;
  int J1axisFault = 0, J2axisFault = 0, J3axisFault = 0;
  int TotalAxisFault = 0;

  int xStart = inData.indexOf("X");
  int yStart = inData.indexOf("Y");
  int zStart = inData.indexOf("Z");
  int SPstart = inData.indexOf("S");
  int AcStart = inData.indexOf("Ac");
  int DcStart = inData.indexOf("Dc");
  int RmStart = inData.indexOf("Rm");

  float targetX = inData.substring(xStart + 1, yStart).toFloat();
  float targetY = inData.substring(yStart + 1, zStart).toFloat();
  float targetZ = inData.substring(zStart + 1, SPstart).toFloat();

  String SpeedType = inData.substring(SPstart + 1, SPstart + 2);
  float SpeedVal = inData.substring(SPstart + 2, AcStart).toFloat();
  float ACCspd = inData.substring(AcStart + 2, DcStart).toFloat();
  float DCCspd = inData.substring(DcStart + 2, RmStart).toFloat();
  float ACCramp = inData.substring(RmStart + 2).toFloat();

  float startX = currentX, startY = currentY, startZ = currentZ;
  float vecX = targetX - startX, vecY = targetY - startY, vecZ = targetZ - startZ;
  float lineDist = sqrt(vecX * vecX + vecY * vecY + vecZ * vecZ);

  if (lineDist <= 0) return;

  const float LIN_WAY_DIST = 1.0;
  int numWaypoints = ceil(lineDist / LIN_WAY_DIST);

  float J1target, J2target, J3target;
  if (delta_calcInverse(targetX, targetY, targetZ, J1target, J2target, J3target) != 0) {
    Serial.println(F("ER"));
    return;
  }

  for (int w = 0; w <= numWaypoints && !systemFault; w++) {
    float t = (float)w / numWaypoints;
    float interpX = startX + vecX * t;
    float interpY = startY + vecY * t;
    float interpZ = startZ + vecZ * t;

    float J1ang, J2ang, J3ang;
    if (delta_calcInverse(interpX, interpY, interpZ, J1ang, J2ang, J3ang) != 0) break;

    int steps1 = abs((J1ang - currentAngles[0]) * STEPS_PER_DEGREE);
    int steps2 = abs((J2ang - currentAngles[1]) * STEPS_PER_DEGREE);
    int steps3 = abs((J3ang - currentAngles[2]) * STEPS_PER_DEGREE);

    J1dir = (J1ang >= currentAngles[0]) ? 1 : 0;
    J2dir = (J2ang >= currentAngles[1]) ? 1 : 0;
    J3dir = (J3ang >= currentAngles[2]) ? 1 : 0;

    float segmentTime = (SpeedType == "s") ? SpeedVal / numWaypoints : lineDist / SpeedVal / numWaypoints;
    int maxSegSteps = max(steps1, max(steps2, steps3));
    float stepDelay = (segmentTime * 1000000) / max(1, maxSegSteps);

    driveMotorsL(steps1, steps2, steps3, J1dir, J2dir, J3dir, stepDelay);

    currentAngles[0] = J1ang;
    currentAngles[1] = J2ang;
    currentAngles[2] = J3ang;
  }

  currentX = targetX;
  currentY = targetY;
  currentZ = targetZ;
  sendRobotPos();
}

void moveCircle(String inData) {

  int xCenterStart = inData.indexOf("Cx");
  int yCenterStart = inData.indexOf("Cy");
  int zCenterStart = inData.indexOf("Cz");
  int xStartStart = inData.indexOf("Bx");
  int yStartStart = inData.indexOf("By");
  int zStartStart = inData.indexOf("Bz");
  int xEndStart = inData.indexOf("Px");
  int yEndStart = inData.indexOf("Py");
  int zEndStart = inData.indexOf("Pz");
  int SPstart = inData.indexOf("S");

  float centerX = inData.substring(xCenterStart + 2, yCenterStart).toFloat();
  float centerY = inData.substring(yCenterStart + 2, zCenterStart).toFloat();
  float centerZ = inData.substring(zCenterStart + 2, xStartStart).toFloat();

  float startX = inData.substring(xStartStart + 2, yStartStart).toFloat();
  float startY = inData.substring(yStartStart + 2, zStartStart).toFloat();
  float startZ = inData.substring(zStartStart + 2, xEndStart).toFloat();

  float endX = inData.substring(xEndStart + 2, yEndStart).toFloat();
  float endY = inData.substring(yEndStart + 2, zEndStart).toFloat();
  float endZ = inData.substring(zEndStart + 2, SPstart).toFloat();

  float SpeedVal = inData.substring(SPstart + 2).toFloat();

  float radius = sqrt(pow(startX - centerX, 2) + pow(startY - centerY, 2) + pow(startZ - centerZ, 2));
  float startAngle = atan2(startY - centerY, startX - centerX);
  float endAngle = atan2(endY - centerY, endX - centerX);

  float angleDiff = endAngle - startAngle;
  if (angleDiff > pi) angleDiff -= 2 * pi;
  if (angleDiff < -pi) angleDiff += 2 * pi;

  int numPoints = 50;

  for (int i = 0; i <= numPoints; i++) {
    float t = (float)i / numPoints;
    float currentAngle = startAngle + angleDiff * t;

    float pointX = centerX + radius * cos(currentAngle);
    float pointY = centerY + radius * sin(currentAngle);
    float pointZ = startZ + (endZ - startZ) * t;

    float j1, j2, j3;
    if (delta_calcInverse(pointX, pointY, pointZ, j1, j2, j3) != 0) continue;

    int steps1 = abs((j1 - currentAngles[0]) * STEPS_PER_DEGREE);
    int steps2 = abs((j2 - currentAngles[1]) * STEPS_PER_DEGREE);
    int steps3 = abs((j3 - currentAngles[2]) * STEPS_PER_DEGREE);

    int dir1 = (j1 >= currentAngles[0]) ? 1 : 0;
    int dir2 = (j2 >= currentAngles[1]) ? 1 : 0;
    int dir3 = (j3 >= currentAngles[2]) ? 1 : 0;

    float segmentTime = SpeedVal / numPoints;
    int maxSteps = max(steps1, max(steps2, steps3));
    float stepDelay = (segmentTime * 1000000) / max(1, maxSteps);

    driveMotorsL(steps1, steps2, steps3, dir1, dir2, dir3, stepDelay);

    currentAngles[0] = j1;
    currentAngles[1] = j2;
    currentAngles[2] = j3;
  }

  currentX = endX;
  currentY = endY;
  currentZ = endZ;
  sendRobotPos();
}

//========== SETUP ==========
void setup() {
  Serial.begin(9600);

  for (int i = 0; i < 3; i++) {
    pinMode(PUL[i], OUTPUT);
    pinMode(DIR[i], OUTPUT);
    pinMode(ENA[i], OUTPUT);
    pinMode(SENSOR[i], INPUT_PULLUP);
    pinMode(ALM[i], INPUT_PULLUP);
    digitalWrite(ENA[i], LOW);
  }

  pinMode(ESTOP_PIN, INPUT_PULLUP);
  attachInterrupt(
    digitalPinToInterrupt(ESTOP_PIN), [] {
      systemFault = true;
    },
    FALLING);

  for (int i = 0; i < 3; i++) {
    stepLimPos[i] = limPos[i] * STEPS_PER_DEGREE;
    stepLimNeg[i] = abs(limNeg[i]) * STEPS_PER_DEGREE;
    zeroStep[i] = stepLimNeg[i];
    stepPos[i] = zeroStep[i];
    calStepOffset[i] = calOffset[i] * STEPS_PER_DEGREE;
  }

  Serial.println(F("DELTA OS INITIALIZED."));
  Serial.println(F("Commands: JC, GOTO x y z time, MJ, ML, MC, RESET"));
}

//========== LOOP ==========
void loop() {
  if (systemFault) {
    for (int i = 0; i < 3; i++) digitalWrite(ENA[i], HIGH);
    Serial.println(F("FAULT ACTIVE. Type 'RESET' to clear."));
    delay(1000);
    return;
  }

  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    String upperCmd = cmd;
    upperCmd.toUpperCase();

    if (upperCmd == "JC") {
      calibrateSynced();
    } else if (upperCmd == "RESET") {
      systemFault = false;
      for (int i = 0; i < 3; i++) digitalWrite(ENA[i], LOW);
      Serial.println(F("SYSTEM_RESET_OK"));
    } else if (upperCmd.startsWith("GOTO")) {
      float x, y, z, t;
      int firstSpace = cmd.indexOf(' ');
      int secondSpace = cmd.indexOf(' ', firstSpace + 1);
      int thirdSpace = cmd.indexOf(' ', secondSpace + 1);
      int fourthSpace = cmd.indexOf(' ', thirdSpace + 1);

      if (firstSpace > 0 && secondSpace > 0 && thirdSpace > 0) {
        x = cmd.substring(firstSpace + 1, secondSpace).toFloat();
        y = cmd.substring(secondSpace + 1, thirdSpace).toFloat();
        z = cmd.substring(thirdSpace + 1, fourthSpace).toFloat();
        t = cmd.substring(fourthSpace + 1).toFloat();

        float t1, t2, t3;
        if (delta_calcInverse(x, y, z, t1, t2, t3) == 0) {
          float targets[] = { t1, t2, t3 };
          syncMove(targets, t);
          currentX = x;
          currentY = y;
          currentZ = z;
          Serial.println(F("DONE"));
        } else {
          Serial.println(F("OUT_OF_RANGE"));
        }
      }
    } else if (upperCmd.startsWith("MJ")) {
      moveJ(cmd, true, false, false);
    } else if (upperCmd.startsWith("MG")) {
      moveJ(cmd, true, false, true);
    } else if (upperCmd.startsWith("ML")) {
      moveLinear(cmd);
    } else if (upperCmd.startsWith("MC")) {
      moveCircle(cmd);
    } else if (cmd.length() > 0) {
      Serial.print(F("Unknown: "));
      Serial.println(cmd);
    }
  }
}