import json
import logging
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
log = logging.getLogger("InfluxBridge")

# MQTT Configuration
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "factory/motor/telemetry"

# InfluxDB Configuration (Must match docker-compose.yml)
INFLUX_URL = "http://127.0.0.1:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "factory"
INFLUX_BUCKET = "telemetry"

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info(f"[*] Connected to MQTT. Subscribing to {MQTT_TOPIC}...")
        client.subscribe(MQTT_TOPIC)
    else:
        log.error(f"[!] MQTT Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # Construct Time-Series Data Point
        point = (
            Point("motor_telemetry")
            .tag("device_id", payload.get("device_id"))
            .field("temperature_c", float(payload.get("temperature_c")))
            .field("vibration_mms", float(payload.get("vibration_mms")))
        )
        
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        log.info(f"[INFLUX WRITE] {payload.get('device_id')} | Temp: {payload.get('temperature_c')} | Vib: {payload.get('vibration_mms')}")
        
    except Exception as e:
        log.error(f"[!] Failed to write to InfluxDB: {e}")

def run_bridge():
    log.info("[*] Starting MQTT to InfluxDB Bridge...")
    mqtt_client = mqtt.Client(client_id="InfluxBridge_01")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

if __name__ == "__main__":
    try:
        run_bridge()
    except KeyboardInterrupt:
        log.info("[*] Bridge stopped by user.")