// Pins
const int micPin = A0;         // Microphone input pin
const int redPin = 9;         // RGB LED - Red
const int greenPin = 10;      // RGB LED - Green
const int bluePin = 11;       // RGB LED - Blue

// Thresholds and timing
const int soundThreshold = 200; // Adjust based on microphone sensitivity
unsigned long lastTalkDetected = 0;
unsigned long totalTalkTime = 0;
unsigned long lastUpdateTime = 0;

// Timers
const unsigned long maxTalkDuration = 10000; // Talking too much (>10s)
const unsigned long silenceDuration = 10000; // Quiet too long (>10s)

bool isTalking = false;

void setup() {
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  Serial.begin(9600);
  lastUpdateTime = millis();
}

void loop() {
  int micValue = analogRead(micPin);
  unsigned long currentTime = millis();
  unsigned long timeElapsed = currentTime - lastUpdateTime;
  lastUpdateTime = currentTime;

  // Detect talking
  if (micValue > soundThreshold) {
    Serial.println("SPEAKING");
    lastTalkDetected = currentTime;
    isTalking = true;
    totalTalkTime += timeElapsed; // Add every loop cycle's duration while talking
  } else {
    isTalking = false;
  }

  // Prioritized LED Feedback
  if ((currentTime - lastTalkDetected) >= silenceDuration) {
    // Talked too much
    setLED(255, 255, 0); // Yellow
  } else if (totalTalkTime > maxTalkDuration) {
    // Quiet for too long
    setLED(255, 0, 0); // Red
  } else {
    // Balanced talking
    setLED(0, 255, 0); // Green
  }

  // Debugging info
  Serial.print("Total Talk Time: ");
  Serial.print(totalTalkTime);
  Serial.print(" ms, Mic: ");
  Serial.println(micValue);

  delay(100);
}

void setLED(int redVal, int greenVal, int blueVal) {
  analogWrite(redPin, redVal);
  analogWrite(greenPin, greenVal);
  analogWrite(bluePin, blueVal);
}
