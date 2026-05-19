# 🏭 Industrial IoT Telemetry Pipeline

An enterprise-grade, decoupled telemetry pipeline designed to extract, transform, and visualize industrial sensor data in real-time. This project demonstrates a complete **Software-in-the-Loop (SIL)** architecture that is ready for **Hardware-in-the-Loop (HIL)** transition.

## 🏗️ Architecture Overview

The system follows a strict decoupled approach to ensure high fault tolerance and maintainability:

1.  **Hardware/Simulator Layer:** Acts as a Modbus TCP Server. Currently supports software simulation or real ESP32/Arduino nodes.
2.  **Edge Gateway Layer:** An asynchronous Modbus client that polls data at 1Hz, performs unit conversion, and publishes JSON payloads via **MQTT**.
3.  **Transport Layer:** **Eclipse Mosquitto** serves as the low-latency message bus.
4.  **Storage & Visualization Layer:** A **Dockerized** stack featuring **InfluxDB v2** (time-series storage) and **Grafana** (industrial dashboarding).

---

## 🛠️ Tech Stack
* **Core:** Python 3.11+, C++ (for Embedded)
* **Protocols:** Modbus TCP, MQTT
* **Infrastructure:** Docker, Docker Compose
* **Tools:** InfluxDB, Grafana, PlatformIO

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have Docker, Docker Compose, and Mosquitto installed on your Linux system.

### 2. Infrastructure Setup
Spin up the database and visualization containers:
```
docker-compose up -d
```
### 3. Service Deployment

Run these services in separate terminal windows (ensure venv is active):

Start the Gateway:
    ```
    python edge_gateway.py
    ```
Start the MQTT-to-Influx Bridge:

```
python mqtt_influx_bridge.py
```
### 4. Visualization
Access Grafana at ```http://localhost:3000``` (admin/5890).
Add ```InfluxDB``` as a Data Source.
Use the Flux query language with the following parameters:

Org: ```factory```

Bucket: ```telemetry```

Token: ```my-super-secret-auth-token```
        
### 🔌 Hardware Integration (HIL)

To connect real hardware (e.g., ESP32):

Flash the ```src/main.cpp``` using PlatformIO.

Update the ```edge_gateway.py``` client to point to your device's static IP and port ```502```.

The rest of the pipeline remains unchanged due to the decoupled architecture.

### 📂 Project Structure
```
.
├── docker-compose.yml       # Infrastructure orchestration
├── edge_gateway.py          # Modbus-to-MQTT logic
├── mqtt_influx_bridge.py    # MQTT-to-InfluxDB bridge
├── modbus_simulator.py      # SIL Simulation logic
├── src/main.cpp             # Embedded C++ firmware
└── platformio.ini           # Embedded project config
```
