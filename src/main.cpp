#include <Arduino.h>
#include <WiFi.h>
#include <ModbusIP_ESP8266.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

ModbusIP mb;
const uint16_t REG_STATUS = 1;
const uint16_t REG_TEMP = 2;
const uint16_t REG_VIB = 3;

#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

Adafruit_MPU6050 mpu;
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL_MS = 1000;

void setup_wifi() {
    Serial.print("[*] Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) { delay(500); }
    Serial.println("\n[+] WiFi connected.");
}

void setup_sensors() {
    tempSensor.begin();
    if (!mpu.begin()) {
        Serial.println("[!] CRITICAL: Failed to find MPU6050");
        while (1) { delay(10); }
    }
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

void setup() {
    Serial.begin(115200);
    setup_wifi();
    setup_sensors();
    mb.server();
    mb.addHreg(REG_STATUS, 1);
    mb.addHreg(REG_TEMP, 0);
    mb.addHreg(REG_VIB, 0);
}

void loop() {
    mb.task();
    unsigned long currentMillis = millis();
    if (currentMillis - lastUpdate >= UPDATE_INTERVAL_MS) {
        lastUpdate = currentMillis;
        tempSensor.requestTemperatures();
        float tempC = tempSensor.getTempCByIndex(0);
        sensors_event_t a, g, temp;
        mpu.getEvent(&a, &g, &temp);
        float accel_magnitude = sqrt(pow(a.acceleration.x, 2) + pow(a.acceleration.y, 2) + pow(a.acceleration.z, 2));
        float vibration_intensity = abs(accel_magnitude - 9.81); 
        mb.Hreg(REG_TEMP, (uint16_t)(tempC * 10.0));
        mb.Hreg(REG_VIB, (uint16_t)(vibration_intensity * 100.0));
    }
}