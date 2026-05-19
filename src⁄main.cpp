#include <Arduino.h>
#include <WiFi.h>
#include <ModbusIP_ESP8266.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// --- Network Configuration ---
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// --- Modbus Configuration ---
ModbusIP mb;
const uint16_t REG_STATUS = 1;
const uint16_t REG_TEMP = 2;
const uint16_t REG_VIB = 3;

// --- Sensor Configuration ---
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

Adafruit_MPU6050 mpu;

// --- Timing Variables ---
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL_MS = 1000;

void setup_wifi() {
    Serial.print("[*] Connecting to WiFi: ");
    Serial.println(WIFI_SSID);
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("");
    Serial.print("[+] WiFi connected. IP Address: ");
    Serial.println(WiFi.localIP());
}

void setup_sensors() {
    Serial.println("[*] Initializing sensors...");
    
    tempSensor.begin();
    
    if (!mpu.begin()) {
        Serial.println("[!] CRITICAL: Failed to find MPU6050 chip");
        while (1) { delay(10); } // Halt execution
    }
    
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    
    Serial.println("[+] Sensors initialized successfully.");
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    setup_wifi();
    setup_sensors();
    
    // Initialize Modbus TCP Server
    mb.server();
    
    // Allocate Holding Registers
    mb.addHreg(REG_STATUS, 1); // 1 = RUNNING
    mb.addHreg(REG_TEMP, 0);
    mb.addHreg(REG_VIB, 0);
    
    Serial.println("[+] Modbus TCP Server running on port 502.");
}

void loop() {
    // Process Modbus network traffic (Non-blocking)
    mb.task();
    
    unsigned long currentMillis = millis();
    if (currentMillis - lastUpdate >= UPDATE_INTERVAL_MS) {
        lastUpdate = currentMillis;
        
        // 1. Read Temperature
        tempSensor.requestTemperatures();
        float tempC = tempSensor.getTempCByIndex(0);
        
        // 2. Read Vibration (Acceleration vector magnitude minus gravity)
        sensors_event_t a, g, temp;
        mpu.getEvent(&a, &g, &temp);
        
        float accel_magnitude = sqrt(pow(a.acceleration.x, 2) + 
                                     pow(a.acceleration.y, 2) + 
                                     pow(a.acceleration.z, 2));
                                     
        // Subtract 1G (approx 9.81 m/s^2) to isolate dynamic vibration
        float vibration_intensity = abs(accel_magnitude - 9.81); 
        
        // 3. Scale values for Modbus transmission (Integers only)
        // Python Gateway expects Temp scaled by 10, Vib scaled by 100
        uint16_t scaled_temp = (uint16_t)(tempC * 10.0);
        uint16_t scaled_vib = (uint16_t)(vibration_intensity * 100.0);
        
        // 4. Write to Modbus Registers
        mb.Hreg(REG_TEMP, scaled_temp);
        mb.Hreg(REG_VIB, scaled_vib);
        
        // 5. Local Telemetry Log
        Serial.printf("[TELEMETRY] Temp: %.2f C | Vib: %.2f m/s^2\n", tempC, vibration_intensity);
    }
}